from ascii_magic import AsciiArt, Back, Front
from pathlib import Path
import re

# --- settings ---
COLUMNS = 80                       # ASCII width
INPUT_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}  # which files to convert

here = Path(__file__).parent
input_dir = here / "CowyDance"
frames_dir = here / "CowyDanceFrame"
frames_dir.mkdir(exist_ok=True)

# Natural sort so "Layer 2.png" comes before "Layer 10.png"
def natural_key(p: Path):
    return [int(s) if s.isdigit() else s.lower() for s in re.findall(r"\d+|\D+", p.name)]

# Collect all images in ElliotJump folder
images = sorted(
    [p for p in input_dir.iterdir() if p.suffix.lower() in INPUT_EXTS],
    key=natural_key
)

if not images:
    print(f"No images found inside: {input_dir}")
else:
    pad = max(3, len(str(len(images))))  # zero-padding width for consistent numbering
    for i, img_path in enumerate(images, start=1):
        print(f"[{i}/{len(images)}] Converting: {img_path.name}")
        art = AsciiArt.from_image(str(img_path))
        out_path = frames_dir / f"{i:0{pad}d}.txt"
        art.to_file(path=str(out_path), columns=COLUMNS, monochrome=True)

    print(f"✅ Done! Saved {len(images)} ASCII frames in: {frames_dir}")