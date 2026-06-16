"""Resolve extracted citations into working authorities (FR-03, FR-04).

eyecite is the primary engine: :func:`eyecite.resolve_citations` groups each full
citation with its short/supra/id references into a cluster, which becomes one
authority. The citetab recognizer (:mod:`citetab.pipeline.supplemental`) fills
eyecite's two gaps; its candidates are merged here, de-duplicated against eyecite
by authority identity so anything eyecite already parsed wins.

Citations eyecite cannot anchor (an orphan short form with no full citation, e.g.
*Ellison* in the dirty fixture) are returned separately as ``unresolved`` — they
are excluded from the TOA and drive TT-001 in the rules phase.

The output is a list of mutable :class:`~citetab.pipeline.working.WorkingAuthority`
objects with their occurrences but no pages yet; pages are filled by the
convergence loop, after which the canonical registry is frozen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import cast

from eyecite import get_citations, resolve_citations
from eyecite.models import (
    CitationBase,
    FullCaseCitation,
    FullLawCitation,
    IdCitation,
    ShortCaseCitation,
    SupraCitation,
)

from citetab.engine.profile_loader import CourtProfile
from citetab.models.registry import AuthorityType, GroupKey, OccurrenceForm
from citetab.pipeline.courts import court_abbreviation
from citetab.pipeline.extractor import BodyText
from citetab.pipeline.parser import ParsedDocument
from citetab.pipeline.supplemental import SupplementalCitation, recognize
from citetab.pipeline.working import WorkingAuthority, WorkingOccurrence


@dataclass(frozen=True)
class ResolveResult:
    """The resolved authorities plus any citations eyecite could not anchor."""

    authorities: list[WorkingAuthority]
    unresolved: list[WorkingOccurrence]


def _form_of(citation: CitationBase) -> OccurrenceForm:
    """Map an eyecite citation type to a registry occurrence form."""
    if isinstance(citation, (FullCaseCitation, FullLawCitation)):
        return "full"
    if isinstance(citation, ShortCaseCitation):
        return "short"
    if isinstance(citation, SupraCitation):
        return "supra"
    if isinstance(citation, IdCitation):
        return "id"
    return "short"


def _pincite(citation: CitationBase) -> str | None:
    """Return the pin cite for a citation, when eyecite captured one."""
    pin = getattr(citation.metadata, "pin_cite", None)
    return str(pin) if pin else None


@dataclass(frozen=True)
class _AuthorityFields:
    """Derived identity/display/sort/components for one authority."""

    type: AuthorityType
    identity: str
    display_full: str
    sort_key: str
    components: dict[str, object]
    display_short: str | None


def _case_fields(cite: FullCaseCitation) -> _AuthorityFields:
    """Derive authority fields for a case citation."""
    groups = cite.groups
    volume = groups.get("volume")
    reporter = groups.get("reporter")
    page = groups.get("page")
    meta = cite.metadata
    plaintiff = getattr(meta, "plaintiff", None)
    defendant = getattr(meta, "defendant", None)
    year = getattr(meta, "year", None)
    court = getattr(meta, "court", None)

    reporter_key = re.sub(r"[^a-z0-9]", "", (reporter or "").casefold())
    identity = f"case:{reporter_key}:{volume}:{page}"

    if plaintiff and defendant:
        name: str | None = f"{plaintiff} v. {defendant}"
    elif plaintiff:
        name = plaintiff
    else:
        name = None

    abbreviation = court_abbreviation(court, reporter)
    if year:
        paren = f"({abbreviation} {year})" if abbreviation else f"({year})"
    else:
        paren = f"({abbreviation})" if abbreviation else ""

    cite_str = f"{volume} {reporter} {page}"
    if name and paren:
        display_full = f"{name}, {cite_str} {paren}"
    elif name:
        display_full = f"{name}, {cite_str}"
    elif paren:
        display_full = f"{cite_str} {paren}"
    else:
        display_full = cite_str

    return _AuthorityFields(
        type="case",
        identity=identity,
        display_full=display_full,
        sort_key=(name or cite_str).casefold(),
        components={
            "volume": volume,
            "reporter": reporter,
            "page": page,
            "court": court,
            "year": year,
            "plaintiff": plaintiff,
            "defendant": defendant,
        },
        display_short=plaintiff,
    )


def _law_fields(cite: FullLawCitation) -> _AuthorityFields:
    """Derive authority fields for a statute/regulation citation."""
    groups = cite.groups
    reporter = groups.get("reporter") or ""
    number = groups.get("title") or groups.get("chapter") or "0"
    section = groups.get("section") or ""
    is_reg = reporter == "C.F.R."
    authority_type: AuthorityType = "regulation" if is_reg else "statute"
    code_key = "cfr" if is_reg else "usc"
    return _AuthorityFields(
        type=authority_type,
        identity=f"{authority_type}:{code_key}:{number}:{section}",
        display_full=f"{number} {reporter} § {section}",
        sort_key=f"{int(number):05d} {section}",
        components={"code": reporter, "number": number, "section": section},
        display_short=None,
    )


def _fields_for_key(cite: CitationBase) -> _AuthorityFields | None:
    """Derive authority fields for a resolution cluster key, or None if unanchorable."""
    if isinstance(cite, FullCaseCitation):
        return _case_fields(cite)
    if isinstance(cite, FullLawCitation):
        return _law_fields(cite)
    return None


def _make_occurrence(citation: CitationBase, body: BodyText) -> WorkingOccurrence:
    """Build a working occurrence (no page yet) from an eyecite citation."""
    start, end = citation.span()
    paragraph_index, char_span = body.to_para_span(start, end)
    return WorkingOccurrence(
        form=_form_of(citation),
        raw_text=citation.matched_text() or "",
        paragraph_index=paragraph_index,
        char_span=char_span,
        pincite=_pincite(citation),
    )


def _supplemental_occurrence(
    candidate: SupplementalCitation, body: BodyText
) -> WorkingOccurrence:
    """Build a working occurrence from a supplemental recognizer candidate."""
    start, end = candidate.span
    paragraph_index, char_span = body.to_para_span(start, end)
    return WorkingOccurrence(
        form="full",
        raw_text=candidate.matched_text,
        paragraph_index=paragraph_index,
        char_span=char_span,
    )


def resolve(
    parsed: ParsedDocument, body: BodyText, profile: CourtProfile
) -> ResolveResult:
    """Resolve the body's citations into working authorities.

    Args:
        parsed: The parsed document (unused directly; kept for symmetry/future).
        body: The concatenated body text and offset map.
        profile: The active court profile (for type → group mapping).

    Returns:
        A :class:`ResolveResult` with the resolved authorities (no pages yet) and
        any citations eyecite could not anchor.
    """
    del parsed  # resolution works off the body text and its offset map
    citations = get_citations(body.text)
    clusters = resolve_citations(citations)

    authorities: dict[str, WorkingAuthority] = {}
    unresolved: list[WorkingOccurrence] = []
    clustered_ids: set[int] = set()

    for resource, members in clusters.items():
        clustered_ids.update(id(member) for member in members)
        key_cite = getattr(resource, "citation", None)
        fields = _fields_for_key(key_cite) if key_cite is not None else None
        if fields is None:
            unresolved.extend(_make_occurrence(c, body) for c in members)
            continue
        group = cast(GroupKey, profile.group_for_type(fields.type))
        authority = authorities.get(fields.identity)
        if authority is None:
            authority = WorkingAuthority(
                authority_id=fields.identity,
                type=fields.type,
                components=fields.components,
                display_full=fields.display_full,
                sort_key=fields.sort_key,
                group=group,
                display_short=fields.display_short,
            )
            authorities[fields.identity] = authority
        authority.occurrences.extend(_make_occurrence(c, body) for c in members)

    # Reference forms eyecite could not anchor to any full citation are dropped
    # from every cluster; collect them as orphans (the TT-001 input).
    for citation in citations:
        if id(citation) in clustered_ids:
            continue
        if isinstance(citation, (ShortCaseCitation, SupraCitation, IdCitation)):
            unresolved.append(_make_occurrence(citation, body))

    _merge_supplemental(authorities, body, profile)

    return ResolveResult(authorities=list(authorities.values()), unresolved=unresolved)


def identify_entry(text: str) -> str | None:
    """Return the authority identity of the primary citation in a TOA entry line.

    Used by the input-TOA diff to match an existing entry to a registry authority
    by *resolved identity*, not string equality (FR-05), so formatting drift
    alone never produces a false missing/phantom finding.

    Args:
        text: The verbatim text of one input-TOA entry.

    Returns:
        The authority identity (matching :attr:`WorkingAuthority.authority_id`),
        or ``None`` if no full case/law/supplemental citation is recognized.
    """
    for citation in get_citations(text):
        fields = _fields_for_key(citation)
        if fields is not None:
            return fields.identity
    candidates = recognize(text)
    return candidates[0].identity if candidates else None


def _merge_supplemental(
    authorities: dict[str, WorkingAuthority],
    body: BodyText,
    profile: CourtProfile,
) -> None:
    """Merge recognizer candidates, skipping identities eyecite already owns."""
    by_identity: dict[str, list[SupplementalCitation]] = {}
    for candidate in recognize(body.text):
        by_identity.setdefault(candidate.identity, []).append(candidate)

    for identity, candidates in by_identity.items():
        if identity in authorities:
            continue  # eyecite already parsed this authority; it owns the occurrences
        first = candidates[0]
        group = cast(GroupKey, profile.group_for_type(first.type))
        authority = WorkingAuthority(
            authority_id=identity,
            type=first.type,
            components={"display": first.display_full},
            display_full=first.display_full,
            sort_key=first.sort_key,
            group=group,
            occurrences=[_supplemental_occurrence(c, body) for c in candidates],
        )
        authorities[identity] = authority
