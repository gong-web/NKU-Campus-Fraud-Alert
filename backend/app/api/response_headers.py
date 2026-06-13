"""HTTP response header helpers."""

from __future__ import annotations

from typing import Literal
from urllib.parse import quote


def content_disposition(
    filename: str,
    *,
    disposition: Literal["inline", "attachment"] = "inline",
    fallback_filename: str = "file",
) -> str:
    """Build an ASCII-only Content-Disposition value with a UTF-8 filename."""
    clean_filename = (
        filename.replace("\r", "").replace("\n", "").rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        or fallback_filename
    )
    ascii_fallback = (
        "".join(
            char
            for char in fallback_filename.replace("\r", "").replace("\n", "")
            if char.isascii() and (char.isalnum() or char in "._-")
        )
        or "file"
    )
    return (
        f'{disposition}; filename="{ascii_fallback}"; '
        f"filename*=UTF-8''{quote(clean_filename, safe='')}"
    )
