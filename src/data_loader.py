"""CSV loading and molecule validation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import List, Optional

import pandas as pd
from rdkit import Chem


@dataclass
class MoleculeDataset:
    """Validated dataset plus row-level diagnostics."""

    data: pd.DataFrame
    smiles_column: str
    molecule_column: str = "_molecule"
    canonical_smiles_column: str = "_canonical_smiles"

    @property
    def valid(self) -> pd.DataFrame:
        return self.data[self.data[self.molecule_column].notna()].copy()

    @property
    def invalid(self) -> pd.DataFrame:
        return self.data[self.data[self.molecule_column].isna()].copy()

    @property
    def duplicate_canonical_smiles(self) -> pd.Series:
        canonical = self.valid[self.canonical_smiles_column]
        return canonical[canonical.duplicated(keep=False)].sort_values()


def read_csv(source) -> pd.DataFrame:
    """Read a path, bytes buffer, or file-like object into a DataFrame."""
    if isinstance(source, (bytes, bytearray)):
        source = BytesIO(source)
    return pd.read_csv(source)


def validate_smiles(data: pd.DataFrame, smiles_column: str) -> MoleculeDataset:
    """Parse SMILES and retain row-level diagnostics without dropping rows."""
    if smiles_column not in data.columns:
        raise ValueError(f"SMILES column not found: {smiles_column}")

    result = data.copy().reset_index(drop=True)
    molecules: List[Optional[Chem.Mol]] = []
    canonical: List[Optional[str]] = []
    for value in result[smiles_column]:
        text = "" if pd.isna(value) else str(value).strip()
        mol = Chem.MolFromSmiles(text) if text else None
        molecules.append(mol)
        canonical.append(Chem.MolToSmiles(mol) if mol is not None else None)

    result["_molecule"] = molecules
    result["_canonical_smiles"] = canonical
    return MoleculeDataset(data=result, smiles_column=smiles_column)
