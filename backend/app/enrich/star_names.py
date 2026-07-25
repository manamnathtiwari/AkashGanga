"""Turn raw solver annotations into user-friendly, named objects.

- Bright stars annotated by Henry Draper number ("HD 12345") get their IAU
  proper name (Vega, Betelgeuse, ...) when known.
- Deep-sky objects (Messier / NGC / IC) keep their catalog name as display name.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from app.solver.base import RawAnnotation

_DATA_FILE = Path(__file__).parent / "data" / "bright_stars.json"
_HD_RE = re.compile(r"HD\s*0*(\d+)", re.IGNORECASE)

# Map raw annotation "type" values to our friendly kinds.
_KIND_MAP = {
    "hd": "star",
    "tycho2": "star",
    "bright": "star",
    "messier": "messier",
    "ngc": "ngc",
    "ic": "ic",
}


@lru_cache
def _hd_name_map() -> dict[str, str]:
    with open(_DATA_FILE, encoding="utf-8") as fh:
        return json.load(fh).get("stars", {})


def _proper_star_name(names: list[str]) -> str | None:
    mapping = _hd_name_map()
    for name in names:
        match = _HD_RE.search(name)
        if match and match.group(1) in mapping:
            return mapping[match.group(1)]
    return None


def enrich_annotation(raw: RawAnnotation) -> dict:
    """Return a dict ready to build an Annotation model row."""
    kind = _KIND_MAP.get(raw.kind.lower(), raw.kind.lower() or "unknown")

    display_name: str | None = None
    if kind == "star":
        display_name = _proper_star_name(raw.names)
    if display_name is None and raw.names:
        display_name = raw.names[0]

    return {
        "kind": kind,
        "names": raw.names,
        "display_name": display_name,
        "pixel_x": raw.pixel_x,
        "pixel_y": raw.pixel_y,
        "radius": raw.radius,
    }


def enrich_annotations(raws: list[RawAnnotation]) -> list[dict]:
    return [enrich_annotation(r) for r in raws]
