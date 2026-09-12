"""Streamlit rendering helpers for molecular structure cards."""

from __future__ import annotations

from html import escape

import streamlit as st
from rdkit.Chem import Draw


def render_selected_molecule_card(
    row,
    smiles_column: str,
    molecule_id_column,
    property_columns,
    position_column: str = "_original_position",
):
    """Render the query molecule without neighbor-only metrics."""
    image = Draw.MolToImage(row["_molecule"], size=(320, 220))
    st.image(image, use_column_width=True)
    st.markdown("**Selected molecule**")
    st.code(str(row[smiles_column]), language=None)
    if molecule_id_column:
        st.caption(f"ID: {row[molecule_id_column]}")
    if position_column in row.index:
        st.caption(f"Dataset row: {int(row[position_column]) + 1}")
    for column in property_columns:
        st.markdown(f"**{escape(str(column))}:** {escape(str(row[column]))}")


def render_molecule_card(row, smiles_column: str, molecule_id_column, property_columns):
    """Render one compact, readable neighbor card."""
    image = Draw.MolToImage(row["_molecule"], size=(260, 180))
    st.image(image, use_column_width=False)
    st.markdown(f"**Rank {int(row['rank'])}**")
    st.code(str(row[smiles_column]), language=None)
    if molecule_id_column:
        st.caption(f"ID: {row[molecule_id_column]}")
    st.metric("Tanimoto similarity", f"{row['similarity']:.4f}")
    st.caption(f"Tanimoto distance: {row['distance']:.4f}")
    for column in property_columns:
        st.markdown(f"**{escape(str(column))}:** {escape(str(row[column]))}")
