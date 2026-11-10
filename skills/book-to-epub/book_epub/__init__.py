"""Compatibility entry point. Canonical implementation moved to skills/booksmith."""
from pathlib import Path

__path__ = [str(Path(__file__).resolve().parents[2] / 'booksmith' / 'book_epub')]
__version__ = '0.2.0'
