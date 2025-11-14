import hyperscan
from .base_engine import RegexEngine
from typing import List, Callable, Any


class HyperscanEngine(RegexEngine):
    COMPILER_MODE_FLAGS = hyperscan.HS_MODE_STREAM | hyperscan.HS_MODE_SOM_HORIZON_LARGE
    COMPILE_FLAGS = hyperscan.HS_FLAG_SOM_LEFTMOST

    def __init__(self):
        self.db = None
        self.patterns = []
    
    def compile_patterns(self, patterns, ids=None):
        self.patterns = patterns
        if ids is None:
            ids = list(range(len(patterns)))
        flags = [HyperscanEngine.COMPILE_FLAGS] * len(patterns)
        self.db = hyperscan.Database(mode=HyperscanEngine.COMPILER_MODE_FLAGS)
        self.db.compile(expressions=patterns, ids=ids, flags=flags, elements=len(patterns))
    
    def scan(self, data, callback):
        if self.db is None:
            raise RuntimeError('Wzorce nie zostaly skompilowane')
        self.db.scan(data, match_event_handler=callback)
    
    def scan_stream(self, data_chunks, callback, context=None):
        if self.db is None:
            raise RuntimeError('Wzorce nie zostaly skompilowane')

        with self.db.stream(match_event_handler=callback, context=context) as stream:
            for chunk in data_chunks:
                stream.scan(chunk)
