"""Unit tests for star-name enrichment."""
from app.enrich.star_names import enrich_annotation, enrich_annotations
from app.solver.base import RawAnnotation


def test_hd_number_maps_to_proper_name():
    raw = RawAnnotation(kind="hd", names=["HD 172167"], pixel_x=10, pixel_y=20, radius=0)
    result = enrich_annotation(raw)
    assert result["kind"] == "star"
    assert result["display_name"] == "Vega"


def test_hd_with_leading_zeros_and_spacing():
    raw = RawAnnotation(kind="hd", names=["HD0048915"], pixel_x=1, pixel_y=1, radius=0)
    assert enrich_annotation(raw)["display_name"] == "Sirius"


def test_unknown_star_falls_back_to_catalog_name():
    raw = RawAnnotation(kind="hd", names=["HD 999999"], pixel_x=1, pixel_y=1, radius=0)
    result = enrich_annotation(raw)
    assert result["display_name"] == "HD 999999"


def test_deep_sky_object_keeps_catalog_name():
    raw = RawAnnotation(kind="messier", names=["M 66"], pixel_x=1, pixel_y=1, radius=0)
    result = enrich_annotation(raw)
    assert result["kind"] == "messier"
    assert result["display_name"] == "M 66"


def test_enrich_list():
    raws = [
        RawAnnotation(kind="hd", names=["HD 172167"], pixel_x=1, pixel_y=1, radius=0),
        RawAnnotation(kind="ngc", names=["NGC 3628"], pixel_x=2, pixel_y=2, radius=0),
    ]
    out = enrich_annotations(raws)
    assert [o["display_name"] for o in out] == ["Vega", "NGC 3628"]
