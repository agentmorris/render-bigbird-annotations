"""
Render annotated thumbnail images from the BigBird dataset.

Draws polygon outlines and species labels on top of source images.
Line thickness and font size are scaled to remain visible when the
image is substantially reduced in size.
"""

import ast
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

JSON_DIR = Path(r"G:\temp\annotated_dataset\annotated_dataset\annotated_dataset")
OUTPUT_DIR = Path(r"G:\temp\bigbird-thumbnails")

# Hand-picked image IDs: 8 top-scoring + 2 high-count
SELECTED = [
    # Top-scoring (large objects, moderate count)
    "1190",  # 1 domestic mallard, huge fraction
    "1189",  # 2 domestic mallards
    "65",    # 4 white storks
    "58",    # 3 white storks
    "37",    # 7 grey herons
    "180",   # 10 gulls (herring + lesser black-backed)
    "589",   # 2 chaco eagles
    "1201",  # 4 dusky moorhen + pacific black duck
    # High object count
    "4810",  # 65 shapes, 4 species (openbill, cormorant, darter, spoonbill)
    "344",   # 79 chinstrap penguins
]

# Distinct colors for cycling across objects
COLORS = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 100, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
    (255, 128, 0),
    (128, 255, 0),
    (0, 128, 255),
    (255, 0, 128),
]


def parse_species(label_str: str) -> str:
    """Extract just the species common name from the label field."""
    if "'name':" in label_str:
        try:
            info = ast.literal_eval(label_str)
            return info.get("name", label_str)
        except Exception:
            pass
    return label_str


def get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a TrueType font at the given size, fall back to default."""
    # Try common Windows fonts
    for name in ("arialbd.ttf", "arial.ttf", "calibrib.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_image(image_id: str) -> None:
    json_path = JSON_DIR / f"{image_id}.json"
    with open(json_path) as f:
        data = json.load(f)

    img_path = JSON_DIR / data["imagePath"]
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Scale line width and font to image size so annotations are visible
    # when the image is shrunk.  Target ~0.15% of the shorter dimension.
    short_side = min(img.width, img.height)
    line_width = max(9, int(short_side * 0.006))
    font_size = max(28, int(short_side * 0.024))
    font = get_font(font_size)

    shapes = data.get("shapes", [])
    # Build a color map per species
    species_list = sorted({parse_species(s["label"]) for s in shapes})
    species_color = {sp: COLORS[i % len(COLORS)] for i, sp in enumerate(species_list)}

    for shape in shapes:
        pts = shape.get("points", [])
        if len(pts) < 3:
            continue

        species = parse_species(shape["label"])
        color = species_color[species]

        # Draw polygon outline
        poly = [(p[0], p[1]) for p in pts]
        draw.polygon(poly, outline=color, width=line_width)

        # Draw label near the top of the polygon
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        label_x = min(xs)
        label_y = min(ys) - font_size - 4
        if label_y < 0:
            label_y = max(ys) + 4

        # Text with dark background for readability
        bbox = draw.textbbox((label_x, label_y), species, font=font)
        pad = 2
        draw.rectangle(
            [bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad],
            fill=(0, 0, 0, 200),
        )
        draw.text((label_x, label_y), species, fill=color, font=font)

    # Save at original resolution
    out_path = OUTPUT_DIR / f"{image_id}.jpg"
    img.save(out_path, quality=95)
    print(f"  Saved {out_path}  ({img.width}x{img.height}, {len(shapes)} annotations)")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Rendering {len(SELECTED)} images to {OUTPUT_DIR}\n")

    for image_id in SELECTED:
        json_path = JSON_DIR / f"{image_id}.json"
        if not json_path.exists():
            print(f"  WARNING: {json_path} not found, skipping")
            continue
        render_image(image_id)

    print("\nDone.")


if __name__ == "__main__":
    main()
