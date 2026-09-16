"""LangTrust: controlled Polish–English security evaluation for tool-using LLM agents."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("langtrust")
except PackageNotFoundError:  # pragma: no cover - editable/source tree edge case
    __version__ = "0.2.0"

__all__ = ["__version__"]
