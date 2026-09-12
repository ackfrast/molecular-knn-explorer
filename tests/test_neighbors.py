import pandas as pd
from rdkit import Chem, DataStructs

from src.fingerprints import generate_fingerprints
from src.neighbors import find_neighbors, mean_knn_distance
from src.visualization import render_selected_molecule_card


def test_neighbors_exclude_self_are_sorted_and_match_direct_rdkit():
    smiles = ["CCO", "CCCO", "CCCCO", "c1ccccc1"]
    molecules = [Chem.MolFromSmiles(value) for value in smiles]
    fingerprints = generate_fingerprints(molecules)
    result = find_neighbors(fingerprints, pd.DataFrame({"smiles": smiles}), selected_position=0, k=3)

    assert 0 not in result["position"].tolist()
    assert result["similarity"].tolist() == sorted(result["similarity"].tolist(), reverse=True)
    direct = DataStructs.TanimotoSimilarity(fingerprints[0], fingerprints[1])
    assert result.iloc[0]["similarity"] == direct
    assert result.iloc[0]["distance"] == 1.0 - direct
    assert mean_knn_distance(result) == result["distance"].mean()


def test_k_larger_than_available_returns_all_other_rows():
    smiles = ["CCO", "CCCO"]
    fingerprints = generate_fingerprints([Chem.MolFromSmiles(value) for value in smiles])
    result = find_neighbors(fingerprints, pd.DataFrame({"smiles": smiles}), selected_position=1, k=10)
    assert len(result) == 1
    assert result.iloc[0]["position"] == 0


def test_selected_card_uses_query_molecule_without_neighbor_fields(monkeypatch):
    row = pd.Series({
        "_molecule": Chem.MolFromSmiles("CCO"),
        "smiles": "CCO",
        "molecule_id": "ethanol",
        "category": "alcohol",
        "_original_position": 0,
    })
    captured = {}

    monkeypatch.setattr("src.visualization.Draw.MolToImage", lambda mol, size: captured.setdefault("mol", mol))
    monkeypatch.setattr("src.visualization.st.image", lambda image, **kwargs: captured.setdefault("image", image))
    monkeypatch.setattr("src.visualization.st.markdown", lambda text: captured.setdefault("markdown", []).append(text))
    monkeypatch.setattr("src.visualization.st.code", lambda text, **kwargs: captured.setdefault("smiles", text))
    monkeypatch.setattr("src.visualization.st.caption", lambda text: captured.setdefault("captions", []).append(text))

    render_selected_molecule_card(row, "smiles", "molecule_id", ["category"])

    assert captured["mol"] is row["_molecule"]
    assert any("Selected molecule" in value for value in captured["markdown"])
    assert captured["smiles"] == "CCO"
    assert any("ID: ethanol" in value for value in captured["captions"])
    assert any("Dataset row: 1" in value for value in captured["captions"])
