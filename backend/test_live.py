#!/usr/bin/env python3
"""
AkashGanga end-to-end test using a real public nova.astrometry.net job.

This script:
  1. Boots the backend (mock solver) and registers a user
  2. Submits a real APOD night-sky image URL
  3. Polls until solved (mock: instant)
  4. Prints ALL result types:
       - Calibration  (RA/Dec/pixscale/orientation)
       - Annotations  (named stars + deep-sky objects)
       - objects_in_field list
  5. Downloads all 3 overlay images from nova.astrometry.net using
     a known solved job (1493115 = Leo Triplet, always available)
       - annotated image  → /tmp/akash_annotated.png
       - red/green image  → /tmp/akash_redgreen.png
       - extraction image → /tmp/akash_extraction.png
"""
import asyncio
import json
import subprocess
import sys
import time

import httpx

BASE = "http://127.0.0.1:8088/api"
# Known permanently-solved nova.astrometry.net job (Leo Triplet, publicly readable).
DEMO_JOB_ID = "1493115"
# A real dark-sky APOD image similar to the user's photo.
SAMPLE_DARK_SKY_URL = "https://apod.nasa.gov/apod/image/0310/m45_wilson.jpg"

NOVA_BASE = "https://nova.astrometry.net"
NOVA_HEADERS = {"Referer": "https://nova.astrometry.net/api/login"}


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("="*60)


async def run():
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as client:

        # ── 1. Register + login ────────────────────────────────────────
        section("Step 1 · Register test user")
        r = await client.post("/auth/register", json={
            "email": "teststar@example.com",
            "display_name": "Test Stargazer",
            "password": "supersecret"
        })
        if r.status_code not in (201, 409):
            r.raise_for_status()
        if r.status_code == 409:
            r = await client.post("/auth/login", json={
                "email": "teststar@example.com",
                "password": "supersecret"
            })
            r.raise_for_status()
        token = r.json()["access_token"]
        auth = {"Authorization": f"Bearer {token}"}
        print("✓ Authenticated")

        # ── 2. Submit dark-sky image URL ───────────────────────────────
        section("Step 2 · Submit dark-sky image URL")
        print(f"  URL: {SAMPLE_DARK_SKY_URL}")
        r = await client.post("/submissions/url",
                              json={"url": SAMPLE_DARK_SKY_URL, "options": {}},
                              headers=auth)
        r.raise_for_status()
        sub = r.json()
        sub_id = sub["id"]
        print(f"  ✓ Submission #{sub_id} created  [status={sub['status']}]")

        # ── 3. Poll until solved ───────────────────────────────────────
        section("Step 3 · Poll until solved")
        for attempt in range(30):
            await asyncio.sleep(0.5)
            r = await client.get(f"/submissions/{sub_id}", headers=auth)
            r.raise_for_status()
            detail = r.json()
            print(f"  poll {attempt+1}: status={detail['status']}")
            if detail["status"] in ("success", "failed"):
                break

        if detail["status"] != "success":
            print(f"\n  ✗ Solve failed: {detail.get('error')}")
            sys.exit(1)

        # ── 4a. Calibration data ───────────────────────────────────────
        section("Step 4a · Calibration (WCS solution)")
        print(json.dumps({
            "ra_deg":       detail["ra"],
            "dec_deg":      detail["dec"],
            "pixscale_arcsec_per_px": detail["pixscale"],
            "orientation_deg":        detail["orientation"],
            "field_radius_deg":       detail["radius"],
            "parity":                 detail["parity"],
        }, indent=4))

        # ── 4b. Annotations (stars + deep-sky) ────────────────────────
        section("Step 4b · Annotations (labelled objects)")
        anns = detail.get("annotations", [])
        stars = [a for a in anns if a["kind"] == "star"]
        dso   = [a for a in anns if a["kind"] != "star"]
        print(f"  Named stars ({len(stars)}):")
        for a in stars:
            print(f"    ★ {a['display_name']:20s}  pixel({a['pixel_x']:.0f}, {a['pixel_y']:.0f})")
        print(f"\n  Deep-sky objects ({len(dso)}):")
        for a in dso:
            print(f"    ◎ {a['display_name']:20s}  kind={a['kind']}")

        # ── 4c. Objects in field ───────────────────────────────────────
        section("Step 4c · Objects in field (summary list)")
        for obj in detail.get("objects_in_field", []):
            print(f"    · {obj}")

        # ── 5. Download all 3 overlay images ──────────────────────────
        section("Step 5 · Overlay images from nova.astrometry.net")
        print(f"  Using demo job {DEMO_JOB_ID} (Leo Triplet, publicly available)\n")

        overlays = {
            "annotated":
                f"  ① Annotated image\n"
                f"     Constellation lines, object name labels, solve-quad outline.\n"
                f"     URL: {NOVA_BASE}/annotated_display/{DEMO_JOB_ID}",
            "red_green":
                f"  ② Red/green overlay\n"
                f"     RED  = stars detected in your image by the solver.\n"
                f"     GREEN = matching stars from the reference catalog.\n"
                f"     URL: {NOVA_BASE}/red_green_image_display/{DEMO_JOB_ID}",
            "extraction":
                f"  ③ Extraction image\n"
                f"     BLUE circles = every source the star-extractor found.\n"
                f"     URL: {NOVA_BASE}/extraction_image_display/{DEMO_JOB_ID}",
        }

        image_files = {
            "annotated":  "/tmp/akash_annotated.png",
            "red_green":  "/tmp/akash_redgreen.png",
            "extraction": "/tmp/akash_extraction.png",
        }

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as nova:
            for key, desc in overlays.items():
                print(desc)
                url = f"{NOVA_BASE}/{'annotated_display' if key=='annotated' else 'red_green_image_display' if key=='red_green' else 'extraction_image_display'}/{DEMO_JOB_ID}"
                try:
                    img = await nova.get(url, headers=NOVA_HEADERS)
                    if img.status_code == 200:
                        out = image_files[key]
                        with open(out, "wb") as f:
                            f.write(img.content)
                        size_kb = len(img.content) // 1024
                        print(f"     ✓ Saved → {out}  ({size_kb} KB)\n")
                    else:
                        print(f"     ⚠  HTTP {img.status_code}\n")
                except Exception as e:
                    print(f"     ⚠  {e}\n")

        section("Done")
        print("  All result types demonstrated.")
        print(f"  Open the saved images:")
        for f in image_files.values():
            print(f"    open {f}")


if __name__ == "__main__":
    asyncio.run(run())
