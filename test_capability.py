import time
import random
import string
import re
import json
import os
from typing import List, Type, Dict, Any, Iterable, Callable

import psutil

from engines.python_engine import PythonEngine
from engines.hs_engine import HyperscanEngine
from file_reader import FileReader


class TextGenerator:
    """
    Text and simple regex generator:
    - first generates “pattern words”
    - then turns them into regexes of the type r"\\bword\\b"
    - generates text with a controlled number of matches:
        match_type = 0 -> no matches
        match_type = 1 -> few matches
        match_type = 2 -> many matches
    """

    def __init__(self, alphabet: str = string.ascii_lowercase):
        self.alphabet = alphabet
        self.pattern_words: List[str] = []
        self.patterns: List[str] = []

    def generate_pattern_words(self, n: int = 5, min_len: int = 4, max_len: int = 8) -> List[str]:
        """Generates n unique pattern words."""
        words = set()
        while len(words) < n:
            length = random.randint(min_len, max_len)
            word = ''.join(random.choice(self.alphabet) for _ in range(length))
            words.add(word)

        self.pattern_words = list(words)
        return self.pattern_words

    def generate_regexes(self) -> List[str]:
        """From pattern_words, create regexes of the type r'\\bword\\b'."""
        if not self.pattern_words:
            raise ValueError("First, call generate_pattern_words().")

        self.patterns = [rf"\b{re.escape(w)}\b" for w in self.pattern_words]
        return self.patterns

    def _generate_random_word(self, min_len: int = 3, max_len: int = 10, forbidden=None) -> str:
        """Generates a random word that does not belong to the forbidden set."""
        if forbidden is None:
            forbidden = set()

        while True:
            length = random.randint(min_len, max_len)
            word = ''.join(random.choice(self.alphabet) for _ in range(length))
            if word not in forbidden:
                return word

    def generate_text(
        self,
        num_lines: int,
        avg_line_len: int,
        match_type: int,
        p_few: float = 0.02,
        p_many: float = 0.4,
    ) -> str:
        """
        Generates multi-line text:
          match_type:
            0 -> no matches
            1 -> few matches (p_few)
            2 -> many matches (p_many)
        avg_line_len is the approximate number of characters per line.
        """
        if not self.pattern_words:
            raise ValueError("First, generate pattern_words and regexes.")

        texts: List[str] = []
        forbidden = set(self.pattern_words)

        for _ in range(num_lines):
            line_words: List[str] = []
            current_len = 0

            while current_len < avg_line_len:
                if match_type == 0:
                    w = self._generate_random_word(forbidden=forbidden)
                elif match_type == 1:
                    if random.random() < p_few:
                        w = random.choice(self.pattern_words)
                    else:
                        w = self._generate_random_word(forbidden=forbidden)
                elif match_type == 2:
                    if random.random() < p_many:
                        w = random.choice(self.pattern_words)
                    else:
                        w = self._generate_random_word(forbidden=forbidden)
                else:
                    raise ValueError("match_type must be 0, 1, or 2.")

                line_words.append(w)
                current_len += len(w) + 1  # +1 for space

            texts.append(" ".join(line_words))

        return "\n".join(texts)


def null_callback(id: int, from_: int, to: int, flags: int, context: Any):
    """Match callback – currently does nothing."""
    pass


def _get_proc() -> psutil.Process:
    return psutil.Process(os.getpid())


def mem_chunks(data: bytes, chunk_size: int = 4096) -> Iterable[bytes]:
    """
    Chunk generator for in-memory data.
    Used to simulate streaming on a big bytes object.
    """
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def benchmark_stream_precompiled(
    engine_cls: Type,
    patterns: List[bytes],
    make_chunks: Callable[[], Iterable[bytes]],
    repeats: int = 5,
) -> Dict[str, Any]:
    """
    Benchmark in STREAM mode:
    - compile patterns only once
    - then multiple scan_stream() calls on chunks from make_chunks()

    make_chunks must be a function that returns a fresh Iterable[bytes]
    each time it is called (e.g. mem_chunks(data) or FileReader.chunks(path)).
    """
    proc = _get_proc()

    # --- compilation ---
    engine = engine_cls()

    cpu_before = proc.cpu_times()
    mem_before = proc.memory_info().rss
    t0 = time.perf_counter()

    engine.compile_patterns(patterns)

    t1 = time.perf_counter()
    cpu_after = proc.cpu_times()
    mem_after = proc.memory_info().rss

    compile_time_wall = t1 - t0
    compile_cpu_user = cpu_after.user - cpu_before.user
    compile_cpu_sys = cpu_after.system - cpu_before.system
    compile_mem_delta = mem_after - mem_before

    # --- streaming scan ---
    scan_times: List[float] = []

    cpu_before_scan = proc.cpu_times()
    mem_before_scan = proc.memory_info().rss

    for _ in range(repeats):
        chunks_iter = make_chunks()

        t_start = time.perf_counter()
        engine.scan_stream(chunks_iter, null_callback, context=None)
        t_end = time.perf_counter()

        scan_times.append(t_end - t_start)

    cpu_after_scan = proc.cpu_times()
    mem_after_scan = proc.memory_info().rss

    scan_cpu_user = cpu_after_scan.user - cpu_before_scan.user
    scan_cpu_sys = cpu_after_scan.system - cpu_before_scan.system
    scan_mem_delta = mem_after_scan - mem_before_scan
    scan_avg_time_wall = sum(scan_times) / len(scan_times) if scan_times else 0.0

    return {
        "engine": engine_cls.__name__,
        "mode": "stream_precompiled",
        "repeats": repeats,
        "compile": {
            "wall_time": compile_time_wall,
            "cpu_user": compile_cpu_user,
            "cpu_sys": compile_cpu_sys,
            "mem_delta": compile_mem_delta,
            "mem_after": mem_after,
        },
        "scan": {
            "times_wall": scan_times,
            "avg_time_wall": scan_avg_time_wall,
            "cpu_user": scan_cpu_user,
            "cpu_sys": scan_cpu_sys,
            "mem_delta": scan_mem_delta,
            "mem_after": mem_after_scan,
        },
    }


def run_generated_text_benchmarks() -> List[Dict[str, Any]]:
    """
    Benchmarks on generated texts (in-memory).
    Uses mem_chunks() to simulate real streaming on big text.
    """
    random.seed(1)

    gen = TextGenerator()
    gen.generate_pattern_words(n=8)
    regex_strs = gen.generate_regexes()

    patterns: List[bytes] = [r.encode("utf-8") for r in regex_strs]

    scenarios = [
        ("small_no_matches", 200, 60, 0),
        ("small_few_matches", 200, 60, 1),
        ("small_many_matches", 200, 60, 2),
        ("large_no_matches", 5000, 80, 0),
        ("large_few_matches", 5000, 80, 1),
        ("large_many_matches", 5000, 80, 2),
    ]

    all_results: List[Dict[str, Any]] = []

    for name, num_lines, avg_len, match_type in scenarios:
        print(f"\n SCENARIO (generated): {name} (match_type={match_type})")

        text_str = gen.generate_text(
            num_lines=num_lines,
            avg_line_len=avg_len,
            match_type=match_type,
        )
        data: bytes = text_str.encode("utf-8")

        # real streaming: multiple chunks in memory
        def make_chunks(d=data):
            return mem_chunks(d, chunk_size=4096)

        for engine_cls in (PythonEngine, HyperscanEngine):
            print(f"  -> Engine: {engine_cls.__name__}")

            res_stream = benchmark_stream_precompiled(engine_cls, patterns, make_chunks, repeats=5)
            res_stream["scenario"] = name
            res_stream["source"] = "generated"

            all_results.append(res_stream)

            print(
                f"     [stream_precompiled]  compile: {res_stream['compile']['wall_time']:.6f}s, "
                f"avg scan: {res_stream['scan']['avg_time_wall']:.6f}s"
            )

    return all_results


def run_file_benchmark(file_path: str) -> List[Dict[str, Any]]:
    """
    Benchmark on a real file using FileReader.chunks().

    Uses:
      make_chunks = lambda: FileReader.chunks(file_path)
    """
    random.seed(1)

    gen = TextGenerator()
    gen.generate_pattern_words(n=8)
    regex_strs = gen.generate_regexes()
    patterns: List[bytes] = [r.encode("utf-8") for r in regex_strs]

    FileReader.validate(file_path)

    all_results: List[Dict[str, Any]] = []

    print(f"\n SCENARIO (file): {file_path}")

    make_chunks = lambda: FileReader.chunks(file_path, chunk_size=FileReader.CHUNK_SIZE)

    for engine_cls in (PythonEngine, HyperscanEngine):
        print(f"  -> Engine: {engine_cls.__name__}")

        res_stream = benchmark_stream_precompiled(engine_cls, patterns, make_chunks, repeats=5)
        res_stream["scenario"] = f"file:{os.path.basename(file_path)}"
        res_stream["source"] = "file"

        all_results.append(res_stream)

        print(
            f"     [stream_precompiled]  compile: {res_stream['compile']['wall_time']:.6f}s, "
            f"avg scan: {res_stream['scan']['avg_time_wall']:.6f}s"
        )

    return all_results


def main():
    results: List[Dict[str, Any]] = []

    # 1) benchmarks on generated texts (always)
    results.extend(run_generated_text_benchmarks())

    # 2) if you want, uncomment and specify the path to a real file:
    # file_results = run_file_benchmark("some_file.log")
    # results.extend(file_results)

    out_file = "benchmark_results_stream.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    main()
