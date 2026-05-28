import json
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict

from mancha.models.cell_type import CellTypeManager
from mancha.models.calibration import Calibration

CONFIG_FILENAME = ".mancha"
CONFIG_VERSION = "0.5"


class Session:
    def __init__(
        self,
        folder: Path,
        cell_types: CellTypeManager,
        calibration: Calibration | None = None,
        classifications: dict[str, dict[int, str]] | None = None,
        version: str = CONFIG_VERSION,
    ):
        self.folder = folder
        self.cell_types = cell_types
        self.calibration = calibration
        self.classifications = classifications or {}
        self.version = version

    @classmethod
    def new(cls, folder: Path) -> "Session":
        return cls(
            folder=folder,
            cell_types=CellTypeManager.create_template(),
        )

    @classmethod
    def load(cls, folder: Path) -> "Session":
        config_path = folder / CONFIG_FILENAME
        if not config_path.exists():
            return cls.new(folder)

        try:
            data = json.loads(config_path.read_text())
        except (json.JSONDecodeError, ValueError):
            corrupted_path = folder / f"{CONFIG_FILENAME}.corrupt"
            shutil.move(str(config_path), str(corrupted_path))
            return cls.new(folder)

        version = data.get("version", CONFIG_VERSION)

        cell_types = CellTypeManager()
        for ct_data in data.get("cell_types", []):
            cell_types.add(ct_data["name"])
            ct = cell_types.types[-1]
            ct.id = ct_data["id"]
            ct.color = tuple(ct_data["color"])

        calibration = None
        if "calibration" in data and data["calibration"]:
            cal = data["calibration"]
            calibration = Calibration(
                units=cal["units"],
                magnitude=cal["magnitude"],
                pixels=cal["pixels"],
            )

        classifications = {}
        for stem, masks in data.get("classifications", {}).items():
            classifications[stem] = {
                int(mask_id): ct_id for mask_id, ct_id in masks.items()
            }

        return cls(
            folder=folder,
            cell_types=cell_types,
            calibration=calibration,
            classifications=classifications,
            version=version,
        )

    def save(self) -> None:
        config_path = self.folder / CONFIG_FILENAME
        data = {
            "version": self.version,
            "cell_types": [
                {"id": ct.id, "name": ct.name, "color": list(ct.color)}
                for ct in self.cell_types.types
            ],
            "calibration": {
                "units": self.calibration.units,
                "magnitude": self.calibration.magnitude,
                "pixels": self.calibration.pixels,
            } if self.calibration else None,
            "classifications": {
                stem: {str(mid): ct_id for mid, ct_id in masks.items()}
                for stem, masks in self.classifications.items()
            },
        }
        config_path.write_text(json.dumps(data, indent=2))

    def classify(self, stem: str, mask_id: int, cell_type_id: str) -> None:
        if stem not in self.classifications:
            self.classifications[stem] = {}
        self.classifications[stem][mask_id] = cell_type_id

    def unclassify(self, stem: str, mask_id: int) -> None:
        if stem in self.classifications:
            self.classifications[stem].pop(mask_id, None)
            if not self.classifications[stem]:
                del self.classifications[stem]

    def get_classification(self, stem: str, mask_id: int) -> str | None:
        return self.classifications.get(stem, {}).get(mask_id)

    def classified_count(self, stem: str) -> int:
        return len(self.classifications.get(stem, {}))
