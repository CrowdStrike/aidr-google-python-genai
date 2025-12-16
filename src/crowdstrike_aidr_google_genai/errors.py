from __future__ import annotations

__all__ = ("CrowdStrikeAidrBlockedError",)


class CrowdStrikeAidrBlockedError(Exception):
    """Raised when CrowdStrike AIDR returns a blocked response."""

    def __init__(self, message: str = "CrowdStrike AIDR returned a blocked response.") -> None:
        super().__init__(message)
