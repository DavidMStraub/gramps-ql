"""Gramps Query Language."""

__version__: str | None
__version_tuple__: tuple[int | str, ...] | None

try:
    # This file is auto-generated, and could be missing.
    from ._version import __version__, __version_tuple__
except ImportError:
    __version__ = None
    __version_tuple__ = None

__all__ = (
    "__version__",
    "__version_tuple__",
    "iter_objects",
    "match",
    "parse",
)

from .gql import iter_objects, match, parse
