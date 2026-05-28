from dataclasses import dataclass


@dataclass(frozen=True)
class Calibration:
    units: str
    magnitude: float
    pixels: float

    @property
    def factor(self) -> float:
        return self.magnitude / self.pixels

    @property
    def area_factor(self) -> float:
        return self.factor ** 2
