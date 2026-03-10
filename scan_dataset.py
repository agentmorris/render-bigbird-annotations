"""
Scan the BigBird dataset to find good candidate images for thumbnail rendering.

Criteria:
- Must have at least 1 annotation (shape)
- Prefer images with large objects (large bounding box area relative to image)
- Prefer a moderate number of objects (not too few, not overwhelming)
- Balance variety of species
"""

import json
import glob
import os
import ast
from pathlib import Path

JSON_DIR = r"G:\temp\annotated_dataset\annotated_dataset\annotated_dataset"


def bbox_area(points):
    """Compute bounding box area from a list of [x, y] points."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def analyze_file(json_path):
    with open(json_path) as f:
        data = json.load(f)

    shapes = data.get("shapes", [])
    if not shapes:
        return None

    img_w = data.get("imageWidth", 1)
    img_h = data.get("imageHeight", 1)
    img_area = img_w * img_h

    # Compute stats per shape
    shape_areas = []
    species_set = set()
    for s in shapes:
        pts = s.get("points", [])
        if len(pts) < 3:
            continue
        area = bbox_area(pts)
        shape_areas.append(area)

        label = s.get("label", "")
        if "'name':" in label:
            try:
                info = ast.literal_eval(label)
                species_set.add(info.get("name", "unknown"))
            except Exception:
                species_set.add(label[:40])
        else:
            species_set.add(label[:40])

    if not shape_areas:
        return None

    max_obj_area = max(shape_areas)
    mean_obj_area = sum(shape_areas) / len(shape_areas)
    max_obj_fraction = max_obj_area / img_area
    mean_obj_fraction = mean_obj_area / img_area

    return {
        "json_path": json_path,
        "image_path": os.path.join(JSON_DIR, data["imagePath"]),
        "num_shapes": len(shapes),
        "img_w": img_w,
        "img_h": img_h,
        "max_obj_area": max_obj_area,
        "mean_obj_area": mean_obj_area,
        "max_obj_fraction": max_obj_fraction,
        "mean_obj_fraction": mean_obj_fraction,
        "species": species_set,
        "original_name": data.get("originalimagePath", ""),
    }


def main():
    json_files = sorted(glob.glob(os.path.join(JSON_DIR, "*.json")))
    print(f"Found {len(json_files)} JSON files")

    results = []
    for jf in json_files:
        info = analyze_file(jf)
        if info is not None:
            results.append(info)

    print(f"Images with annotations: {len(results)}")

    # Print distribution
    from collections import Counter
    shape_counts = Counter(r["num_shapes"] for r in results)
    print("\nShape count distribution:")
    for k in sorted(shape_counts.keys()):
        print(f"  {k}: {shape_counts[k]}")

    # Collect all species
    all_species = set()
    for r in results:
        all_species.update(r["species"])
    print(f"\nAll species ({len(all_species)}): {sorted(all_species)}")

    # Sort by a score that balances large objects and moderate count
    # We want: large max_obj_fraction (objects visible at thumbnail size)
    #          moderate num_shapes (say 2-15 is ideal)
    #          variety of species across the 10 selected
    for r in results:
        count = r["num_shapes"]
        # Prefer 2-10 shapes; penalize 1 and >15
        if count == 1:
            count_score = 0.5
        elif 2 <= count <= 10:
            count_score = 1.0
        elif 11 <= count <= 20:
            count_score = 0.7
        else:
            count_score = 0.3
        r["score"] = r["max_obj_fraction"] * count_score

    results.sort(key=lambda r: r["score"], reverse=True)

    print("\n=== Top 30 candidates ===")
    for i, r in enumerate(results[:30]):
        species_str = ", ".join(sorted(r["species"]))
        print(
            f"{i+1:3d}. {os.path.basename(r['json_path']):>10s}  "
            f"shapes={r['num_shapes']:3d}  "
            f"max_frac={r['max_obj_fraction']:.4f}  "
            f"mean_frac={r['mean_obj_fraction']:.6f}  "
            f"score={r['score']:.4f}  "
            f"size={r['img_w']}x{r['img_h']}  "
            f"species=[{species_str}]"
        )

    # Save full results for the rendering script
    import pickle
    with open("scan_results.pkl", "wb") as f:
        pickle.dump(results, f)
    print(f"\nSaved {len(results)} results to scan_results.pkl")


if __name__ == "__main__":
    main()
