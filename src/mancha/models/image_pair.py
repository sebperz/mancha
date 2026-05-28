from pathlib import Path
from dataclasses import dataclass

from tifffile import imread
from PIL import Image as PILImage

SOURCE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


@dataclass
class ImagePair:
    source_path: Path
    mask_path: Path
    stem: str


@dataclass
class ValidationWarning:
    level: str
    message: str
    file: Path | None


def discover_pairs(folder: Path) -> tuple[list[ImagePair], list[ValidationWarning]]:
    pairs: list[ImagePair] = []
    warnings: list[ValidationWarning] = []

    mask_files = sorted(folder.glob("*_masks.tif"))

    for mask_path in mask_files:
        mask_name = mask_path.name
        stem = mask_name.removesuffix("_masks.tif")

        source_path = _find_source(folder, stem)

        if source_path is None:
            warnings.append(ValidationWarning(
                level="missing_source",
                message=f"No source image found for {mask_name}",
                file=mask_path,
            ))
            continue

        if not _dimensions_match(source_path, mask_path):
            warnings.append(ValidationWarning(
                level="size_mismatch",
                message=f"Source and mask dimensions differ for {stem}",
                file=source_path,
            ))
            continue

        pairs.append(ImagePair(
            source_path=source_path,
            mask_path=mask_path,
            stem=stem,
        ))

    return pairs, warnings


def _find_source(folder: Path, stem: str) -> Path | None:
    stem_lower = stem.lower()
    for f in folder.iterdir():
        if not f.is_file():
            continue
        if f.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        if f.stem.lower() == stem_lower:
            return f
    return None


def _dimensions_match(source_path: Path, mask_path: Path) -> bool:
    mask = imread(mask_path)
    with PILImage.open(source_path) as img:
        source_h, source_w = img.height, img.width
    return mask.shape[:2] == (source_h, source_w)
