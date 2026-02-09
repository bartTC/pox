"""Utility functions for pox."""

import textwrap


def dedent(text: str) -> str:
    """Dedent the given text and remove leading and trailing whitespace."""
    return textwrap.dedent(text).strip()


def box_message(text: str) -> str:
    """
    Add a decorative line on the left side of the given message.

    The last line uses a thicker marker.
    """
    lines = text.splitlines(keepends=True)

    if len(lines) == 1:
        return f"╼ {text}"

    return "".join(
        (
            f"┍ {lines[0]}",
            *(f"│ {line}" for line in lines[1:-1]),
            f"┕ {lines[-1]}",
        ),
    )


def remove_control_characters(s: str) -> str:
    """Remove control characters and whitespace from the string."""
    replace = ["\\", "\n", "\r", "\t", " "]
    for r in replace:
        s = s.replace(r, "")
    return s
