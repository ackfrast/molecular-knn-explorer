"""Morgan/ECFP fingerprint generation."""

from __future__ import annotations

from typing import Iterable

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator


def morgan_generator(radius: int = 2, n_bits: int = 1024):
    """Return RDKit's current Morgan fingerprint generator."""
    if radius < 0 or n_bits <= 0:
        raise ValueError("radius must be >= 0 and n_bits must be > 0")
    return rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)


def generate_fingerprints(molecules: Iterable[Chem.Mol], radius: int = 2, n_bits: int = 1024):
    """Generate deterministic ExplicitBitVect fingerprints for valid molecules."""
    generator = morgan_generator(radius, n_bits)
    return [generator.GetFingerprint(mol) for mol in molecules]


def fingerprints_to_numpy(fingerprints) -> np.ndarray:
    """Convert RDKit fingerprints to a 2D NumPy array for inspection/testing."""
    if not fingerprints:
        return np.empty((0, 0), dtype=np.uint8)
    result = np.zeros((len(fingerprints), fingerprints[0].GetNumBits()), dtype=np.uint8)
    for row, fingerprint in enumerate(fingerprints):
        DataStructs.ConvertToNumpyArray(fingerprint, result[row])
    return result
