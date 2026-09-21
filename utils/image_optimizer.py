"""
FREE Image Optimizer - JPG to WebP, 70% smaller
Uses Pillow (free, already in requirements)

Usage:
  python utils/image_optimizer.py
"""
from pathlib import Path
from PIL import Image


def optimize():
    src = Path("static/images")
    out = src / "optimized"
    out.mkdir(exist_ok=True)

    total_saved = 0
    for img_path in src.glob("*.jpg"):
        if img_path.parent.name == "optimized":
            continue
        try:
            img = Image.open(img_path)
            img = img.convert("RGB")

            # WebP
            webp = out / f"{img_path.stem}.webp"
            img.save(webp, "WEBP", quality=80, method=6)

            # Thumb
            thumb = img.copy()
            thumb.thumbnail((400, 400))
            thumb_path = out / f"{img_path.stem}-thumb.webp"
            thumb.save(thumb_path, "WEBP", quality=75)

            orig = img_path.stat().st_size
            new = webp.stat().st_size
            saved = orig - new
            total_saved += saved

            print(f"✅ {img_path.name}: {orig // 1024}KB -> {new // 1024}KB (saved {saved // 1024}KB)")
        except Exception as e:
            print(f"❌ {img_path.name}: {e}")

    print(f"\n💰 Total saved: {total_saved // 1024}KB - Faster site, FREE!")


if __name__ == "__main__":
    optimize()
