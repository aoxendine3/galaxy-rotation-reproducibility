# Galaxy Rotation Curve Reproducibility Package

This repository contains the complete, reviewer-ready code, data, and documentation to reproduce the Navarro–Frenk–White (NFW) dark matter halo fit for the spiral galaxy **NGC 2403**, using observational data from the SPARC database.

## Directory Overview

```
galaxy_rotation_reproducibility/
├── data/
│   ├── sparc_ngc2403.csv       # Raw rotation-curve measurements (SPARC)
│   └── checksums.txt           # Verified SHA-256 hashes of all assets
├── src/
│   ├── preprocess.py           # Preprocessing and helper routines
│   └── model_fit.py            # Non-linear NFW fitting & plot generation
├── figures/
│   ├── rotation_curve_fit.jpg  # Generated data and model fit plot
│   └── rotation_curve_residuals.jpg # Generated fit residuals plot
├── scripts/
│   └── download_data.py        # Python utility to fetch NGC 2403 data from SPARC
├── tests/
│   └── test_pipeline.py        # Automated pytest validation suite
├── .github/workflows/
│   └── ci.yml                  # GitHub Actions continuous integration pipeline
├── requirements.txt            # Python dependencies (NumPy, SciPy, Pandas, Matplotlib)
├── README.md                   # This overview file
└── report.md                   # Detailed scientific reproducibility report
```

## Quick Start

### 1. Install Dependencies
Ensure you have Python 3.10+ installed. In a clean virtual environment, run:
```bash
pip install -r requirements.txt
```

### 2. Download SPARC Observational Data
Acquire and format the official NGC 2403 data file from the SPARC catalog:
```bash
python3 scripts/download_data.py
```

### 3. Run Fitting Analysis and Generate Figures
Perform the non-linear NFW fit and write the plots to `figures/`:
```bash
python3 src/model_fit.py data/sparc_ngc2403.csv
```

### 4. Run Verification Suite
Execute the automated test suite to verify data integrity, fitting precision, and file presence:
```bash
PYTHONPATH=. pytest -q
```

All steps are documented in [report.md](report.md).
