from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPixmap, QPolygonF, QPen, QBrush, QColor
from PySide6.QtCore import Qt, QPointF, Signal

from skimage.measure import find_contours
from tifffile import imread
import numpy as np

from mancha.models.image_pair import ImagePair

UNCLASSIFIED_COLOR = (128, 128, 128)
UNCLASSIFIED_ALPHA = 76
OUTLINE_DARKEN_FACTOR = 0.5
ZOOM_FACTOR = 1.15


def _darker(c: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(int(v * OUTLINE_DARKEN_FACTOR) for v in c)


class Viewport(QGraphicsView):
    mask_left_clicked = Signal(int)
    mask_right_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHints(self.renderHints())

        self.mask_items: list = []
        self._mask_id_to_items: dict[int, list] = {}
        self._colors: dict[int, tuple[int, int, int]] = {}
        self._mask_array: np.ndarray | None = None
        self._pixmap_item = None
        self.selected_mask_id: int | None = None

    def load_pair(self, pair: ImagePair) -> None:
        self._clear()
        self._pixmap_item = self.scene().addPixmap(
            QPixmap(str(pair.source_path))
        )
        self._mask_array = imread(pair.mask_path)
        self._add_mask_overlays()
        self.fit_to_window()

    def fit_to_window(self) -> None:
        self.fitInView(
            self.scene().itemsBoundingRect(), Qt.KeepAspectRatio
        )

    def set_cell_type_colors(
        self, colors: dict[int, tuple[int, int, int]]
    ) -> None:
        self._colors = colors
        for mask_id, items in self._mask_id_to_items.items():
            r, g, b = colors.get(mask_id, UNCLASSIFIED_COLOR)
            brush = QBrush(QColor(r, g, b, UNCLASSIFIED_ALPHA))
            pen = QPen(QColor(*_darker((r, g, b))))
            for item in items:
                item.setBrush(brush)
                item.setPen(pen)

    def hide_masks(self) -> None:
        for item in self.mask_items:
            item.setVisible(False)

    def show_masks(self) -> None:
        for item in self.mask_items:
            item.setVisible(True)

    def mousePressEvent(self, event) -> None:
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            scene_pos = self.mapToScene(event.position().toPoint())
            mask_id = self._mask_id_at(scene_pos)
            if mask_id > 0:
                self.selected_mask_id = mask_id
                if event.button() == Qt.LeftButton:
                    self.mask_left_clicked.emit(mask_id)
                else:
                    self.mask_right_clicked.emit(mask_id)
                return
        super().mousePressEvent(event)

    def _mask_id_at(self, scene_pos: QPointF) -> int:
        if self._mask_array is None:
            return 0
        x = int(scene_pos.x())
        y = int(scene_pos.y())
        h, w = self._mask_array.shape
        if 0 <= x < w and 0 <= y < h:
            return int(self._mask_array[y, x])
        return 0

    def _clear(self) -> None:
        self.scene().clear()
        self.mask_items.clear()
        self._mask_id_to_items.clear()
        self._colors.clear()
        self._mask_array = None
        self._pixmap_item = None
        self.selected_mask_id = None

    def _add_mask_overlays(self) -> None:
        if self._mask_array is None:
            return
        masks = self._mask_array
        mask_ids = np.unique(masks[masks > 0])
        default_pen = QPen(QColor(*_darker(UNCLASSIFIED_COLOR)))
        default_brush = QBrush(QColor(*UNCLASSIFIED_COLOR, UNCLASSIFIED_ALPHA))

        for mask_id in mask_ids:
            mask_id = int(mask_id)
            binary = (masks == mask_id).astype(np.uint8)
            contours = find_contours(binary, level=0.5)
            items = []
            for contour in contours:
                polygon = QPolygonF()
                for y, x in contour:
                    polygon.append(QPointF(float(x), float(y)))
                item = self.scene().addPolygon(
                    polygon, default_pen, default_brush
                )
                items.append(item)
                self.mask_items.append(item)
            self._mask_id_to_items[mask_id] = items

    def wheelEvent(self, event) -> None:
        if event.angleDelta().y() > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _zoom_in(self) -> None:
        self.scale(ZOOM_FACTOR, ZOOM_FACTOR)

    def _zoom_out(self) -> None:
        self.scale(1 / ZOOM_FACTOR, 1 / ZOOM_FACTOR)
