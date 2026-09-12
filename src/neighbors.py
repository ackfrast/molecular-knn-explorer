"""Within-dataset Tanimoto nearest-neighbor calculations."""

from __future__ import annotations

from typing import Sequence

import pandas as pd
from rdkit import DataStructs


def find_neighbors(fingerprints: Sequence, data: pd.DataFrame, selected_position: int, k: int) -> pd.DataFrame:
    """Return top-k neighbors, excluding the selected row itself."""
    if not 0 <= selected_position < len(fingerprints):
        raise IndexError("selected_position is outside the fingerprint collection")
    if len(data) != len(fingerprints):
        raise ValueError("data and fingerprints must have the same length")
    if k < 1:
        raise ValueError("k must be >= 1")

    query = fingerprints[selected_position]
    records = []
    for position, fingerprint in enumerate(fingerprints):
        if position == selected_position:
            continue
        similarity = float(DataStructs.TanimotoSimilarity(query, fingerprint))
        records.append({"position": position, "similarity": similarity, "distance": 1.0 - similarity})

    result = pd.DataFrame(records)
    if result.empty:
        return result.assign(rank=pd.Series(dtype=int))
    result = result.sort_values(["similarity", "position"], ascending=[False, True], kind="mergesort")
    result = result.head(k).reset_index(drop=True)
    result.insert(0, "rank", result.index + 1)
    return result


def mean_knn_distance(neighbors: pd.DataFrame) -> float:
    """Return the mean distance of the displayed neighbors."""
    if neighbors.empty:
        return float("nan")
    return float(neighbors["distance"].mean())
