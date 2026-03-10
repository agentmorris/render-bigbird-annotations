# Big Bird Annotation Thumbnails

Renders sample annotated images from the [Big Bird](https://huggingface.co/datasets/Big-Bird) drone-based bird detection dataset. Polygon annotations (in [Labelme](https://github.com/wkentaro/labelme/) format) are drawn on top of the source images with species labels.

## Dataset

The dataset contains ~4,824 drone images with Labelme JSON annotations. 612 images have at least one annotation, covering 68 bird species. Annotations are polygons outlining individual birds, with metadata including species, age, posture, and taxonomic classification.

## Image Selection

`scan_dataset.py` scans all JSON files and scores each image based on:

- **Object size**: largest annotation bounding box area as a fraction of image area (bigger objects are more visible in thumbnails)
- **Object count**: moderate counts (2-10) are preferred, with a penalty for single-object or very high-count images

Ten images were selected: 8 top-scoring images with moderate annotation counts, plus 2 high-count images (65 and 79 annotations) to demonstrate flock detection.

## Rendering

`render_thumbnails.py` draws annotations on the source images:

- Polygon outlines (no fill), with line thickness scaled to ~0.6% of the image's shorter dimension
- Species labels in bold font scaled to ~2.4% of the shorter dimension
- Dark background rectangles behind labels for readability
- Colors assigned per species

Output is saved at original image resolution as JPEG (quality 95).

## Usage

```bash
pip install -r requirements.txt
python scan_dataset.py        # scan dataset, write scan_results.pkl
python render_thumbnails.py   # render 10 selected images
```

Output is written to `G:\temp\bigbird-thumbnails`.

## Selected Images

| File | Annotations | Species |
|------|-------------|---------|
| 1190 | 1 | domestic mallard |
| 1189 | 2 | domestic mallard |
| 65 | 4 | white stork |
| 58 | 3 | white stork |
| 37 | 7 | grey heron |
| 180 | 10 | european herring gull, lesser black-backed gull |
| 589 | 2 | chaco eagle |
| 1201 | 4 | dusky moorhen, pacific black duck |
| 4810 | 65 | african openbill, reed cormorant, african darter, african spoonbill |
| 344 | 79 | chinstrap penguin |
