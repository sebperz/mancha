from mancha.models.cell_type import CellTypeManager, CellType, TABLEAU_10


def test_empty_manager_has_zero_types():
    manager = CellTypeManager()
    assert manager.types == []
    assert manager.count == 0


def test_add_returns_cell_type_with_color():
    manager = CellTypeManager()
    ct = manager.add("Cell Type 1")

    assert ct.name == "Cell Type 1"
    assert ct.id == "cell_type_1"
    assert isinstance(ct.color, tuple)
    assert len(ct.color) == 3
    assert manager.count == 1
    assert manager.types[0] == ct


def test_sequential_adds_get_distinct_colors():
    manager = CellTypeManager()
    ct1 = manager.add("A")
    ct2 = manager.add("B")

    assert ct1.color != ct2.color
    assert ct1.color == TABLEAU_10[0]
    assert ct2.color == TABLEAU_10[1]


def test_rename_preserves_id_and_color():
    manager = CellTypeManager()
    ct = manager.add("Cell Type 1")
    original_id = ct.id
    original_color = ct.color

    manager.rename(ct.id, "Neuron")

    assert ct.name == "Neuron"
    assert ct.id == original_id
    assert ct.color == original_color
    assert manager.get(ct.id).name == "Neuron"


def test_remove_deletes_type():
    manager = CellTypeManager()
    ct = manager.add("Cell Type 1")
    assert manager.count == 1

    manager.remove(ct.id)

    assert manager.count == 0
    assert manager.get(ct.id) is None


def test_get_returns_none_for_unknown():
    manager = CellTypeManager()
    assert manager.get("nonexistent") is None


def test_beyond_palette_generates_colors():
    manager = CellTypeManager()
    types = [manager.add(f"Type {i}") for i in range(12)]

    for t in types:
        assert isinstance(t.color, tuple)
        assert len(t.color) == 3

    assert types[10].color not in TABLEAU_10
    assert types[11].color not in TABLEAU_10


def test_template_factory():
    manager = CellTypeManager.create_template()

    assert manager.count == 2
    assert manager.types[0].name == "Cell Type 1"
    assert manager.types[1].name == "Cell Type 2"
    assert manager.types[0].color == TABLEAU_10[0]
    assert manager.types[1].color == TABLEAU_10[1]
