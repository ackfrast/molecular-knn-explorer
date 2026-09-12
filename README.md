# Molecular kNN Explorer

A compact Streamlit application for exploring within-dataset molecular nearest neighbors with Morgan/ECFP fingerprints and Tanimoto similarity.

## Windows quick start

For a normal Windows 10/11 64-bit computer:

1. Download the repository as a ZIP from GitHub.
2. Extract the ZIP completely to a local folder. Paths containing spaces or Chinese characters are supported.
3. Double-click `Install-Windows.bat`. It downloads Micromamba and creates the project-local `.molecular-knn-env` with Python, RDKit, Streamlit, pandas, NumPy, PyArrow, and pytest.
4. When installation finishes, double-click `Run-Windows.bat`.

The installer does not require an existing Python or Conda installation and does not modify other research environments. Internet access is required only for the first installation. The environment is kept inside the extracted project folder and is ignored by Git.

The launcher binds only to `127.0.0.1`, tries port 8501 first, and selects another local port if needed. It waits for Streamlit's health endpoint before opening the default browser and prints the exact URL. Keep the launcher window open while using the app; press `Ctrl+C` there to stop the process started by that launcher. It never terminates an unrelated process occupying a port.

To run without opening a browser, use PowerShell from the extracted folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-local.ps1 -NoBrowser
```

If startup fails, inspect `.local-temp\*.log` and rerun the installer if the environment is incomplete. The installer and launcher scripts are project-local; they do not share the existing `chemprop`, `chemprop2`, `molML`, or `molml` environments.

This first iteration supports CSV upload, SMILES validation, invalid/duplicate reporting, manual `k`, self-excluding neighbor search, structure cards, selected dataset properties, and mean kNN distance. It intentionally does not include model prediction, uncertainty quantification, OOD classification, train/test comparison, or automatic `k` recommendation.

## Setup

The tested local setup is a project-local `.venv` based on Python 3.10 and RDKit 2025.09.6:

```bash
/home/b12504112/anaconda3/envs/chemprop2/bin/python -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
```

`requirements.txt` is also suitable for a fresh compatible environment where RDKit is available from conda-forge.

## Run

```bash
.venv/bin/streamlit run app.py
```

Open the printed local URL, upload a CSV, select its SMILES column, choose a molecule and `k`, then inspect the top-k cards. The included example dataset can be loaded from the app.

## Test

```bash
.venv/bin/pytest -q
```

The tests verify deterministic Morgan fingerprints, invalid and duplicate handling, direct RDKit Tanimoto agreement, descending similarity order, and exclusion of the selected row.
