# Mancha

Desktop tool for classifying and measuring cells in microscopy images, using masks pre-segmented by Cellpose-SAM.

<p align="center">
  <img src="https://img.shields.io/badge/version-0.5.0-blue" alt="Version 0.5.0">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20windows-lightgrey" alt="Cross-platform">
</p>

---

## Overview

Mancha is a cross-platform desktop application for scientists who need to classify and measure individual cells in microscopy images. It takes images pre-segmented by the Cellpose-SAM AI model and provides an interactive interface for:

- **Classifying cells** — click on cell masks to assign them to user-defined cell types
- **Measuring morphology** — area, major/minor axis, Feret diameter, perimeter, circularity
- **Exporting data** — timestamped CSV files with traceability over the source image

### Workflow

```
Microscope images  =>  Cellpose-SAM (Colab)  =>  _masks.tif  =>  Mancha  =>  CSV
```

## Quick Start

### Step 1: Generate Masks with Cellpose-SAM

Use the included `cellpose_sam.ipynb` notebook in **Google Colab**:

1. Open [Google Colab](https://colab.research.google.com/) and upload `cellpose_sam.ipynb`
2. Enable GPU: **Runtime > Change runtime type > GPU**
3. Mount your Google Drive and upload your microscope images (`.jpg`, `.png`)
4. Run all cells to segment your images
5. Download the output folder -- each image will have a corresponding `_masks.tif` file

### Step 2: Install Mancha

```bash
pip install -e .
```

### Step 3: Classify and Measure

```bash
python -m mancha
```

1. Click **Select Image Folder** and choose the folder containing your image pairs
2. Enter the **calibration** (e.g., "100 pixels = 10 um")
3. **Left-click** on a mask to assign the selected cell type
4. **Right-click** on a classified mask to unclassify it
5. Press **Space** or **->** for next image, **<-** for previous
6. **File > Export CSV** to save your measurements

### Folder Structure

Your image folder must contain pairs of source images and their corresponding mask files:

```
my_experiment/
  image_01.jpg
  image_01_masks.tif
  image_02.jpg
  image_02_masks.tif
  ...
```

Mancha automatically finds matching pairs and validates their dimensions.

## Features

| Feature | Description |
|---------|-------------|
| **Cell Classification** | Left-click to assign cell types, right-click to unclassify |
| **Custom Cell Types** | Create, rename, and delete cell types with auto-assigned colors |
| **Measurements** | Area, major/minor axis, Feret diameter, perimeter, circularity |
| **Calibration** | Convert pixel measurements to real-world units (um, mm, etc.) |
| **Undo/Redo** | Full Ctrl+Z / Ctrl+Y command stack |
| **Session Persistence** | Auto-saves classification state in the image folder |
| **CSV Export** | Timestamped CSV with one row per classified mask |
| **Zoom & Pan** | Scroll to zoom, drag to pan, F key to fit |
| **Keyboard Shortcuts** | Numbers 1-9 for cell types, arrows/Space for navigation |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1`-`9` | Select Cell Type 1-9 |
| `Left Arrow` `Right Arrow` `Space` | Previous / Next image |
| `F` | Fit image to window |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+O` | Open folder |
| `Ctrl+E` | Export CSV |
| `Ctrl+Q` | Quit |
| `Ctrl+=` / `Ctrl+-` | Zoom in / out |
| `Shift` (hold) | Temporarily hide masks |

## CSV Output

Exported files (`mancha-YYYYMMDD.csv`) contain:

| Column | Description |
|--------|-------------|
| `image` | Source image filename |
| `mask_id` | Integer mask identifier |
| `cell_type` | User-assigned cell type name |
| `area` | Area in calibrated units |
| `major_axis` | Major axis length |
| `minor_axis` | Minor axis length |
| `feret` | Maximum Feret (caliper) diameter |
| `feret_min` | Minimum Feret diameter |
| `perimeter` | Perimeter |
| `circularity` | 4pi x area / perimeter^2 (1.0 = circle) |
| `calibration` | Conversion factor used |
| `edge_cell` | Whether the mask touches the image border |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run against sample data
python -m mancha
# Select the sampleData/ folder
```

## Requirements

- Python 3.10+
- PySide6 (Qt)
- numpy, scikit-image, tifffile

## License

MIT -- see [LICENSE](LICENSE)
