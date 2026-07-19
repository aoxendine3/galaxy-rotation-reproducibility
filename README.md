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
├── pyproject.toml                  # Project packaging and metadata
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
Execute the automated test suite (verifying checksums, parameters, figure generation, and DOI resolution):
```bash
PYTHONPATH=. pytest -v
```

### 5. Advanced Usage: CLI Customization
The fitting script `src/model_fit.py` supports customizing parameter overrides:
```bash
python3 src/model_fit.py data/sparc_ngc2403.csv \
    --upsilon-disk 0.5 \
    --upsilon-bulge 0.5 \
    --p0 12.0 0.008 \
    --bounds 0.1 1e-6 150.0 2.0 \
    --output-fit figures/custom_fit.jpg \
    --output-res figures/custom_res.jpg
```
Run `python3 src/model_fit.py --help` for the full list of options.

### Tested Environments
- **Operating Systems:** macOS 14/15, Ubuntu 20.04/22.04/latest (GitHub Actions).
- **Python Versions:** 3.10, 3.11, 3.12, 3.13, 3.14.6.

### License & Citations
- **Code License:** MIT License.
- **Data License:** CC-BY-4.0 (SPARC Database).
- **Citation:** 
  If you use this work, please cite the SPARC master database publication:
  > Lelli, F., McGaugh, S. S., & Schombert, J. M. (2016). *SPARC: Mass Models for 175 Disk Galaxies with Spitzer Photometry and Accurate Rotation Curves.* The Astronomical Journal, 152(6), 157. DOI: [10.3847/0004-6256/152/6/157](https://doi.org/10.3847/0004-6256/152/6/157)

All detailed scientific findings and assumptions are documented in [report.md](report.md).
