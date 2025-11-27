from abc import ABC, abstractmethod
from typing import List, Callable, Any, Iterable


class RegexEngine(ABC):
    """Abstract base class for regex engines"""
    
    @abstractmethod
    def compile_patterns(self, patterns: List[bytes], ids: List[int] = None) -> None:
        """Compiles regex patterns"""
        pass
    
    @abstractmethod
    def scan(self, data: bytes, callback: Callable) -> None:
        """Scans data and triggers a callback when a match is found"""
        pass
    
    @abstractmethod
    def scan_stream(self, data_chunks: Iterable[bytes], callback: Callable, context: Any = None) -> None:
        """Scans data in streaming mode - accepts iterable chunks of data"""
        pass
