from abc import ABC, abstractmethod
import zlib


class AbstractCompressor(ABC):
    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        """
        Compress bytes.
        """

    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress bytes.
        """


class ZlibCompressor(AbstractCompressor):
    def compress(self, data: bytes) -> bytes:
        """
        Compress bytes using zlib.
        """
        return zlib.compress(data)

    def decompress(self, data: bytes) -> bytes:
        """
        Decompress bytes using zlib.
        """
        return zlib.decompress(data)
