"""Engine cross-cutting components: data-path resolution and loaders.

- :mod:`toatool.engine.resources` resolves the bundled-or-repo paths for the
  versioned ``rules``, ``profiles``, and ``schemas`` data.
- :mod:`toatool.engine.profile_loader` validates a court profile YAML into a
  typed :class:`~toatool.engine.profile_loader.CourtProfile`.
- :mod:`toatool.engine.rule_loader` parses and validates rule-card frontmatter
  and detects drift between active cards and their implementations.

These make Principle 8.5 ("specification before implementation") executable:
nothing about TOA formatting is hardcoded, and a card without a matching
implementation (or vice versa) fails loudly at startup.
"""

from __future__ import annotations
