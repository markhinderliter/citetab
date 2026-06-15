"""citetab's deterministic citation recognizer — the owned seam over eyecite.

eyecite is the primary parser, but it has two gaps the v1 court profile requires:

1. **Subsection-letter statutes.** eyecite's law-section regex accepts dotted,
   hyphenated, and parenthesized sections but not a bare trailing letter, so
   ``15 U.S.C. § 1692e`` (the FDCPA section central to every fixture) parses as
   an ``UnknownCitation``. This recognizer matches full U.S.C./C.F.R. citations
   including a trailing-letter section.
2. **Court rules.** eyecite does not model rules of procedure at all
   (``Fed. R. App. P. 28`` → nothing), yet the FRAP profile has a ``rules``
   group and ``Authority.type`` includes ``rule``.

We deliberately own and version this layer here rather than patching
``reporters_db`` internals: the regexes are narrow, documented, deterministic,
and matched against valid Bluebook formats only. The :mod:`citetab.pipeline.resolver`
merges these candidates with eyecite's output, de-duplicating by authority
identity so anything eyecite already parsed (``28 U.S.C. § 1331``,
``12 C.F.R. § 1006.14``) is taken from eyecite, not duplicated here.

Scope is intentionally conservative: only *full* statutory, regulatory, and rule
citations are recognized. Short statutory references ("section 1692e") and rule
short forms are out of v1 scope, consistent with eyecite not resolving them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from citetab.models.registry import AuthorityType

#: Recognizer version. This is the citetab-owned seam; bumping it signals a
#: change in what the supplemental layer recognizes (its own mini-track).
RECOGNIZER_VERSION = "1.0.0"

# A section identifier: leading digits, then any number of letter runs, dotted
# numeric parts, hyphenated parts, or parenthesized subsections. Written so it
# can never capture trailing punctuation (e.g. "1692e." stops before the dot).
_SECTION = r"\d+(?:[A-Za-z]+|\.\d+|-[A-Za-z0-9]+|\([A-Za-z0-9]+\))*"

_STATUTE_RE = re.compile(
    r"(?P<number>\d+)\s+(?P<code>U\.S\.C\.|C\.F\.R\.)\s*§\s*(?P<section>"
    + _SECTION
    + r")"
)

# Federal rules of procedure/evidence. The set abbreviation is normalized to its
# canonical spaced form for display.
_RULE_RE = re.compile(
    r"(?P<set>Fed\.\s*R\.\s*(?:App\.\s*P\.|Civ\.\s*P\.|Crim\.\s*P\.|Evid\.|Bankr\.\s*P\.))"
    r"\s*(?P<number>\d+(?:\.\d+)?(?:\([A-Za-z0-9]+\))*)"
)


@dataclass(frozen=True)
class SupplementalCitation:
    """A citation recognized by the supplemental layer (not by eyecite)."""

    type: AuthorityType
    identity: str
    """Stable identity used to de-duplicate against eyecite and group occurrences."""

    display_full: str
    sort_key: str
    matched_text: str
    span: tuple[int, int]


def _normalize_rule_set(raw: str) -> str:
    """Collapse whitespace in a rule-set abbreviation to its canonical form."""
    return re.sub(r"\s+", " ", raw).strip()


def _statute_candidate(match: re.Match[str]) -> SupplementalCitation:
    """Build a statute/regulation candidate from a statute regex match."""
    number = match.group("number")
    code = match.group("code")
    section = match.group("section")
    is_reg = code == "C.F.R."
    authority_type: AuthorityType = "regulation" if is_reg else "statute"
    code_key = "cfr" if is_reg else "usc"
    return SupplementalCitation(
        type=authority_type,
        identity=f"{authority_type}:{code_key}:{number}:{section}",
        display_full=f"{number} {code} § {section}",
        sort_key=f"{int(number):05d} {section}",
        matched_text=match.group(0),
        span=match.span(),
    )


def _rule_candidate(match: re.Match[str]) -> SupplementalCitation:
    """Build a court-rule candidate from a rule regex match."""
    rule_set = _normalize_rule_set(match.group("set"))
    number = match.group("number")
    set_key = re.sub(r"[^a-z0-9]", "", rule_set.casefold())
    return SupplementalCitation(
        type="rule",
        identity=f"rule:{set_key}:{number}",
        display_full=f"{rule_set} {number}",
        sort_key=f"{set_key} {number}",
        matched_text=match.group(0),
        span=match.span(),
    )


def recognize(text: str) -> list[SupplementalCitation]:
    """Recognize supplemental citations (statutes, regulations, rules) in ``text``.

    Args:
        text: The body text to scan.

    Returns:
        All supplemental citation candidates, in order of appearance. Identity
        de-duplication against eyecite happens in the resolver, not here.
    """
    candidates: list[SupplementalCitation] = [
        _statute_candidate(m) for m in _STATUTE_RE.finditer(text)
    ]
    candidates += [_rule_candidate(m) for m in _RULE_RE.finditer(text)]
    candidates.sort(key=lambda c: c.span[0])
    return candidates
