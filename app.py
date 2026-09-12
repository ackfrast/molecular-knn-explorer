"""Streamlit entry point for Molecular kNN Explorer."""

from pathlib import Path

import streamlit as st

from src.data_loader import read_csv, validate_smiles
from src.fingerprints import generate_fingerprints
from src.neighbors import find_neighbors, mean_knn_distance
from src.visualization import render_molecule_card, render_selected_molecule_card


DEFAULT_RADIUS = 2
DEFAULT_N_BITS = 1024

st.set_page_config(page_title="Molecular kNN Explorer", page_icon="🧬", layout="wide")
st.title("Molecular kNN Explorer")
st.caption("Within-dataset nearest neighbors using Morgan/ECFP fingerprints and Tanimoto similarity.")

uploaded = st.file_uploader("Upload a CSV file", type="csv")
if uploaded is None:
    example_path = Path(__file__).parent / "examples" / "example_molecules.csv"
    st.info("No file uploaded. Load the included example dataset to try the app.")
    if st.button("Load example dataset"):
        st.session_state["example_data"] = example_path.read_bytes()
    source = st.session_state.get("example_data")
else:
    source = uploaded.getvalue()

if source is None:
    st.stop()

try:
    raw = read_csv(source)
except Exception as exc:
    st.error(f"Could not read CSV: {exc}")
    st.stop()

if raw.empty:
    st.error("The CSV contains no rows.")
    st.stop()

smiles_default_index = next((i for i, column in enumerate(raw.columns) if "smiles" in str(column).lower()), 0)
smiles_column = st.selectbox("SMILES column", list(raw.columns), index=smiles_default_index)
dataset = validate_smiles(raw, smiles_column)
valid = dataset.valid

invalid_count = len(dataset.invalid)
duplicate_count = int(dataset.duplicate_canonical_smiles.size)
if invalid_count:
    st.warning(f"Invalid SMILES: {invalid_count} row(s) excluded from neighbor search.")
    with st.expander("Show invalid rows"):
        st.dataframe(dataset.invalid.drop(columns=["_molecule", "_canonical_smiles"]))
if duplicate_count:
    st.info(f"Duplicate canonical SMILES detected in {duplicate_count} valid row(s). Rows are retained and identified by dataset position.")

if valid.empty:
    st.error("No valid molecules are available for search.")
    st.stop()

with st.sidebar:
    st.header("Fingerprint and search")
    radius = st.number_input("Morgan radius", min_value=0, max_value=8, value=DEFAULT_RADIUS, step=1)
    n_bits = st.number_input("Fingerprint nBits", min_value=128, max_value=8192, value=DEFAULT_N_BITS, step=128)
    max_k = max(1, len(valid) - 1)
    k = st.number_input("Number of neighbors (k)", min_value=1, max_value=max_k, value=min(5, max_k), step=1)

display_columns = [column for column in raw.columns if column != smiles_column]
molecule_id_column = st.selectbox("Molecule ID column (optional)", ["None"] + display_columns)
molecule_id_column = None if molecule_id_column == "None" else molecule_id_column
property_columns = st.multiselect("Additional properties to display", [column for column in display_columns if column != molecule_id_column])

valid = valid.reset_index(drop=False).rename(columns={"index": "_original_position"})
labels = [f"{i}: {row[smiles_column]}" for i, row in valid.iterrows()]
selected_display = st.selectbox("Select a molecule", labels)
selected_position = labels.index(selected_display)

fingerprints = generate_fingerprints(valid["_molecule"], radius=int(radius), n_bits=int(n_bits))
neighbors = find_neighbors(fingerprints, valid, selected_position, int(k))
selected = valid.iloc[selected_position]

st.subheader("Selected molecule")
selected_columns = st.columns([2, 1], gap="medium")
with selected_columns[0]:
    render_selected_molecule_card(selected, smiles_column, molecule_id_column, property_columns)
with selected_columns[1]:
    st.metric("Mean kNN distance", f"{mean_knn_distance(neighbors):.4f}" if not neighbors.empty else "n/a")
    st.caption(f"Valid molecules: {len(valid)}")
    st.caption("The selected molecule is the query reference and is excluded from neighbor search.")

if neighbors.empty:
    st.info("No other valid molecules are available for neighbor search.")
else:
    st.subheader("Top-k nearest neighbors")
    columns = st.columns(min(3, len(neighbors)))
    for card_index, (_, neighbor) in enumerate(neighbors.iterrows()):
        neighbor_row = valid.iloc[int(neighbor["position"])].copy()
        for field in ["rank", "similarity", "distance"]:
            neighbor_row[field] = neighbor[field]
        with columns[card_index % len(columns)]:
            render_molecule_card(neighbor_row, smiles_column, molecule_id_column, property_columns)
