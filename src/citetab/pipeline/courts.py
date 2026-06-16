"""Court abbreviations for case display, sourced from courts-db.

eyecite reports a court as an id (``ca9``, ``wash``, ``scotus``); the TOA needs
the Bluebook citation string (``9th Cir.``, ``Wash.``). courts-db (Free Law
Project, the same provenance as eyecite) is the authoritative source and is
already an eyecite dependency. By convention a U.S. Supreme Court citation omits
the court parenthetical (the ``U.S.`` reporter implies it), so this returns
``None`` for SCOTUS.
"""

from __future__ import annotations

from functools import cache

from courts_db import courts

_SCOTUS_IDS = frozenset({"scotus"})


@cache
def _citation_strings() -> dict[str, str]:
    """Map each court id to its Bluebook citation string (cached)."""
    mapping: dict[str, str] = {}
    for court in courts:
        court_id = court.get("id")
        citation_string = court.get("citation_string")
        if court_id and citation_string:
            mapping[court_id] = citation_string
    return mapping


def court_abbreviation(court_id: str | None, reporter: str | None) -> str | None:
    """Return the court parenthetical abbreviation, or ``None`` to omit it.

    Args:
        court_id: The eyecite court id (e.g. ``ca9``), or ``None``.
        reporter: The reporter abbreviation (e.g. ``U.S.``, ``F.3d``).

    Returns:
        The Bluebook court string (``9th Cir.``), or ``None`` when the court is
        unknown or is the U.S. Supreme Court (whose parenthetical is omitted).
    """
    if court_id in _SCOTUS_IDS or reporter == "U.S.":
        return None
    if court_id is None:
        return None
    return _citation_strings().get(court_id)
