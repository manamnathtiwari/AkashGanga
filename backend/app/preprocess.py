"""Image preprocessing for dark / phone-camera night-sky photos.

Phone cameras (especially Android) heavily compress and underexpose night
shots.  Before sending to nova.astrometry.net we:

  1. Detect whether the image is "dark" (mean brightness < DARK_THRESHOLD).
  2. If dark, apply an arcsinh stretch (standard astrophotography technique)
     that amplifies faint stars relative to the sky background while keeping
     pixel structure intact.
  3. Down-sample large images (> MAX_PIXELS) so nova processes them faster.
  4. Re-export as JPEG to keep file size reasonable.

This is transparent to the rest of the pipeline — the preprocessed file is
saved to a temp path and the original is preserved unchanged.
"""
from __future__ import annotations

import logging
import os
import tempfile

logger = logging.getLogger("akashganga.preprocess")

# Images with mean luminance below this value (0–255) are considered dark.
DARK_THRESHOLD = 30.0
# Maximum total pixel count before we downsample.
MAX_PIXELS = 4_000_000  # 4 MP
STRETCH_FACTOR = 50.0   # higher = brighter faint stars


def _needs_preprocessing(path: str) -> tuple[bool, float]:
    """Return (needs_preprocess, mean_brightness)."""
    try:
        import numpy as np
        from PIL import Image

        img = Image.open(path).convert("L")
        arr = np.array(img, dtype=np.float32)
        mean = float(arr.mean())
        return mean < DARK_THRESHOLD, mean
    except Exception:
        return False, 0.0


def preprocess_image(path: str) -> str:
    """Return a path to the image ready for submission.

    If the image is bright enough and small enough, returns *path* unchanged.
    Otherwise, saves a preprocessed copy to a temp file and returns that path.
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        logger.warning("Pillow/numpy not installed — skipping preprocessing")
        return path

    needs_dark_fix, mean = _needs_preprocessing(path)

    img = Image.open(path)
    w, h = img.size
    total_pixels = w * h
    needs_resize = total_pixels > MAX_PIXELS

    if not needs_dark_fix and not needs_resize:
        return path  # nothing to do

    logger.info(
        "Preprocessing %s  (mean=%.1f  dark=%s  pixels=%d  resize=%s)",
        os.path.basename(path),
        mean,
        needs_dark_fix,
        total_pixels,
        needs_resize,
    )

    img = img.convert("L")  # grayscale — easier for star extractor
    arr = np.array(img, dtype=np.float32)

    if needs_dark_fix:
        # Subtract sky background (robust median estimate), then arcsinh-stretch.
        bg = float(np.percentile(arr, 50))
        sub = np.clip(arr - bg, 0, None)
        peak = sub.max() or 1.0
        stretched = (
            np.arcsinh(sub * STRETCH_FACTOR / peak)
            / np.arcsinh(STRETCH_FACTOR)
            * 255.0
        )
        arr = np.clip(stretched, 0, 255)

    if needs_resize:
        # Downsample so total pixel count ≤ MAX_PIXELS.
        scale = (MAX_PIXELS / total_pixels) ** 0.5
        new_w, new_h = int(w * scale), int(h * scale)
        img = Image.fromarray(arr.astype("uint8")).resize(
            (new_w, new_h), Image.LANCZOS
        )
    else:
        img = Image.fromarray(arr.astype("uint8"))

    # Write to a temp file (caller is responsible for cleanup if desired).
    fd, tmp_path = tempfile.mkstemp(suffix=".jpg", prefix="akash_pre_")
    os.close(fd)
    img.save(tmp_path, format="JPEG", quality=92)
    logger.info("Preprocessed → %s (%d KB)", tmp_path, os.path.getsize(tmp_path) // 1024)
    return tmp_path
