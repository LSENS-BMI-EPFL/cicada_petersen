"""cicada-petersen: Petersen lab extensions for CICADA."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cicada-petersen")
except PackageNotFoundError:     # not installed (e.g. run from a source checkout)
    __version__ = "unknown"
