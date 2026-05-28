from collections.abc import Callable


class UndoManager:
    def __init__(self):
        self._undo_stack: list[tuple[Callable[[], None], Callable[[], None]]] = []
        self._redo_stack: list[tuple[Callable[[], None], Callable[[], None]]] = []

    def push(
        self, do: Callable[[], None], undo: Callable[[], None]
    ) -> None:
        self._undo_stack.append((do, undo))
        self._redo_stack.clear()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        do, undo = self._undo_stack.pop()
        undo()
        self._redo_stack.append((do, undo))
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        do, undo = self._redo_stack.pop()
        do()
        self._undo_stack.append((do, undo))
        return True

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
