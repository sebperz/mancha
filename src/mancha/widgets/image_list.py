from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem

from mancha.models.image_pair import ImagePair
from mancha.models.session import Session


class ImageList(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("Images")
        self._label.setStyleSheet("font-weight: bold;")

        self._list = QListWidget()

        layout.addWidget(self._label)
        layout.addWidget(self._list)

    def load(self, pairs: list[ImagePair], session: Session) -> None:
        self._list.clear()
        for i, pair in enumerate(pairs):
            count = session.classified_count(pair.stem)
            text = f"{pair.source_path.name}  ({count} classified)"
            item = QListWidgetItem(text)
            item.setData(1, i)
            self._list.addItem(item)

    @property
    def list_widget(self):
        return self._list
