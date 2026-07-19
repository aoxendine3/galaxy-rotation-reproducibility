# Galaxy Rotation Curve Reproducibility Package

This repository contains all code, data, and documentation needed to reproduce the analysis of the NGC 2403 rotation curve using the SPARC dataset.

## Directory Overview

```
├── data/                     # Raw data and checksums
├── src/                      # Source code
│   ├── preprocess.py
│   ├── model_fit.py
│   └── figures/
│       ├── rotation_curve_fit.py
│       ├── rotation_curve_residuals.py
│       └── interference_patterns.py
├── figures/                  # Generated figures (run the scripts to create)
├── scripts/                  # Helper scripts (e.g., download data)
├── tests/                    # Test suite
├── requirements.txt          # Exact Python dependencies
├── README.md                 # This file
└── report.md                 # Full reproducibility report
```

## How to Use

1. Install the dependencies from `requirements.txt`.
2. Run `scripts/download_data.sh` to fetch the SPARC CSV files.
3. Execute `python -m src.model_fit` to perform the analysis.
4. Generate the figures with the scripts in `src/figures/`.
5. Run `pytest -q tests/` to verify the pipeline.

All steps are documented in `report.md` with exact commands and expected outputs.
