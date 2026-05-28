from pathlib import Path
from mancha.models.session import Session
from mancha.utils.undo import UndoManager


def test_single_undo_restores_state():
    history = []
    manager = UndoManager()

    def do():
        history.append("done")

    def undo():
        history.pop()

    manager.push(do, undo)
    do()
    assert history == ["done"]

    result = manager.undo()
    assert result is True
    assert history == []


def test_single_redo_restores_after_undo():
    history = []
    manager = UndoManager()

    def do():
        history.append("x")

    def undo():
        history.pop()

    manager.push(do, undo)
    do()
    manager.undo()
    assert history == []

    result = manager.redo()
    assert result is True
    assert history == ["x"]


def test_multiple_undos():
    history = []
    manager = UndoManager()

    def push_and_execute(ch):
        def do():
            history.append(ch)
        def undo():
            history.pop()
        manager.push(do, undo)
        do()

    for ch in "abc":
        push_and_execute(ch)

    assert history == ["a", "b", "c"]

    manager.undo()
    assert history == ["a", "b"]
    manager.undo()
    assert history == ["a"]
    manager.undo()
    assert history == []


def test_new_action_clears_redo_stack():
    history = []
    manager = UndoManager()

    def make_a():
        history.append("a")

    def undo_a():
        history.pop()

    def make_b():
        history.append("b")

    def undo_b():
        history.pop()

    manager.push(make_a, undo_a)
    make_a()
    manager.undo()
    manager.push(make_b, undo_b)
    make_b()

    result = manager.redo()
    assert result is False
    assert history == ["b"]


def test_undo_classification(tmp_path: Path):
    session = Session.new(tmp_path)
    ct = session.cell_types.types[0]
    manager = UndoManager()

    session.classify("img", 3, ct.id)
    manager.push(
        do=lambda: session.classify("img", 3, ct.id),
        undo=lambda: session.unclassify("img", 3),
    )
    assert session.get_classification("img", 3) == ct.id

    manager.undo()
    assert session.get_classification("img", 3) is None

    manager.redo()
    assert session.get_classification("img", 3) == ct.id


def test_undo_unclassification(tmp_path: Path):
    session = Session.new(tmp_path)
    ct = session.cell_types.types[0]

    session.classify("img", 3, ct.id)
    session.unclassify("img", 3)
    assert session.get_classification("img", 3) is None

    manager = UndoManager()
    manager.push(
        do=lambda: session.unclassify("img", 3),
        undo=lambda: session.classify("img", 3, ct.id),
    )

    manager.undo()
    assert session.get_classification("img", 3) == ct.id
