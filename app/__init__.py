"""Shadow Writer — scout grounded research + social drafting."""

from typing import TYPE_CHECKING

__version__ = "0.1.0"
__all__ = ["ResearchSession", "__version__"]

if TYPE_CHECKING:
    from research_session import ResearchSession


def __getattr__(name: str):
    if name == "ResearchSession":
        from research_session import ResearchSession

        return ResearchSession
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
