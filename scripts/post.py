"""Cinematic post: subtle bloom, cold-shadow grade, vignette, grain."""
import sys, os
import numpy as np
from PIL import Image, ImageFilter


def process(src, dst, bloom_strength=0.42, bloom_radius=30, grain=0.005,
            vignette=0.2, sharpen=True):
    img = Image.open(src).convert('RGB')
    arr = np.asarray(img).astype(np.float32) / 255.0
    h, w = arr.shape[:2]
    # bloom on highlights
    lum = arr.max(axis=2)
    mask = np.clip((lum - 0.68) / 0.32, 0.0, 1.0) ** 1.7
    bright = arr * mask[..., None]
    b = Image.fromarray((np.clip(bright, 0, 1) * 255).astype(np.uint8))
    b = b.filter(ImageFilter.GaussianBlur(bloom_radius))
    b = np.asarray(b).astype(np.float32) / 255.0
    out = 1.0 - (1.0 - arr) * (1.0 - b * bloom_strength)
    # cool shadows, warm highlights
    l = out.mean(axis=2, keepdims=True)
    out = out + (1.0 - l) * np.array([0.012, 0.026, 0.055], dtype=np.float32) \
              + l * np.array([0.035, 0.010, -0.018], dtype=np.float32)
    # gentle contrast and saturation
    out = (out - 0.44) * 1.055 + 0.44 + 0.006
    out = np.clip(out, 0, 1)
    gray = out.mean(axis=2, keepdims=True)
    out = gray + (out - gray) * 1.07
    # vignette
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    v = 1.0 - vignette * np.clip((r - 0.5) / 0.7, 0, 1) ** 1.5
    out *= v[..., None]
    if grain:
        rng = np.random.default_rng(7)
        out += rng.normal(0, grain, out.shape).astype(np.float32)
    out = np.clip(out, 0, 1)
    im = Image.fromarray((out * 255).astype(np.uint8))
    if sharpen:
        im = im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=55, threshold=2))
    im.save(dst, optimize=True)
    print('wrote', dst, im.size)


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'renders/preview.png'
    dst = sys.argv[2] if len(sys.argv) > 2 else src.replace('.png', '_post.png')
    process(src, dst)
