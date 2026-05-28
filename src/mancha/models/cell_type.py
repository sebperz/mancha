from dataclasses import dataclass
import colorsys

TABLEAU_10 = [
    (31, 119, 180),
    (255, 127, 14),
    (44, 160, 44),
    (214, 39, 40),
    (148, 103, 189),
    (140, 86, 75),
    (227, 119, 194),
    (127, 127, 127),
    (188, 189, 34),
    (23, 190, 207),
]


@dataclass
class CellType:
    id: str
    name: str
    color: tuple[int, int, int]


class CellTypeManager:
    def __init__(self):
        self._types: list[CellType] = []
        self._next_color_index = 0

    @classmethod
    def create_template(cls) -> "CellTypeManager":
        manager = cls()
        manager.add("Cell Type 1")
        manager.add("Cell Type 2")
        return manager

    @property
    def types(self) -> list[CellType]:
        return list(self._types)

    @property
    def count(self) -> int:
        return len(self._types)

    def add(self, name: str) -> CellType:
        type_id = self._generate_id(name)
        color = self._next_color()
        ct = CellType(id=type_id, name=name, color=color)
        self._types.append(ct)
        return ct

    def get(self, type_id: str) -> CellType | None:
        for ct in self._types:
            if ct.id == type_id:
                return ct
        return None

    def remove(self, type_id: str) -> None:
        self._types = [ct for ct in self._types if ct.id != type_id]

    def rename(self, type_id: str, new_name: str) -> None:
        ct = self.get(type_id)
        if ct is not None:
            ct.name = new_name

    def _generate_id(self, name: str) -> str:
        base_id = name.lower().replace(" ", "_")
        existing_ids = {t.id for t in self._types}
        if base_id not in existing_ids:
            return base_id
        i = 2
        while f"{base_id}_{i}" in existing_ids:
            i += 1
        return f"{base_id}_{i}"

    def _next_color(self) -> tuple[int, int, int]:
        if self._next_color_index < len(TABLEAU_10):
            color = TABLEAU_10[self._next_color_index]
            self._next_color_index += 1
            return color
        i = self._next_color_index - len(TABLEAU_10)
        self._next_color_index += 1
        h = (i * 0.618033988749895) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.7, 0.9)
        return (int(r * 255), int(g * 255), int(b * 255))
