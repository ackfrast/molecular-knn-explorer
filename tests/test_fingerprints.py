import numpy as np
from rdkit import Chem

from src.fingerprints import fingerprints_to_numpy, generate_fingerprints


def test_morgan_fingerprint_shape_and_determinism():
    molecules = [Chem.MolFromSmiles("CCO"), Chem.MolFromSmiles("CCCO")]
    first = generate_fingerprints(molecules, radius=2, n_bits=1024)
    second = generate_fingerprints(molecules, radius=2, n_bits=1024)
    first_array = fingerprints_to_numpy(first)
    second_array = fingerprints_to_numpy(second)
    assert first_array.shape == (2, 1024)
    assert first_array.dtype == np.uint8
    np.testing.assert_array_equal(first_array, second_array)


def test_invalid_and_duplicate_smiles_are_reported():
    import pandas as pd
    from src.data_loader import validate_smiles

    dataset = validate_smiles(pd.DataFrame({"smiles": ["CCO", "not_smiles", "CCO"]}), "smiles")
    assert len(dataset.valid) == 2
    assert len(dataset.invalid) == 1
    assert dataset.duplicate_canonical_smiles.tolist() == ["CCO", "CCO"]
