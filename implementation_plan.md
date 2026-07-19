# Implementation Plan for Galaxy Rotation Curve Reproducibility Package

## Goal Description
Create a reviewer‑ready, end‑to‑end reproducibility package for the galaxy rotation curve analysis. This includes a comprehensive `report.md` with all required sections, verification of all DOIs, checksums, and repository paths, inclusion of generated figures (`rotation_curve_fit.jpg`, `rotation_curve_residuals.jpg`), and a final integrity check.

## User Review Required
> [!IMPORTANT]
> Review the proposed structure and confirm any additional sections or specific formatting preferences (e.g., citation style, figure caption style). Also confirm whether you want the report to be split into separate files (e.g., `abstract.md`, `methods.md`) or kept as a single `report.md`.

## Open Questions
> [!WARNING]
> 1. Preferred citation style (APA, Chicago, etc.)?
> 2. Should the checksum file be updated with SHA‑256 hashes for each data and figure file?
> 3. Include CI configuration (GitHub Actions) to automatically verify checksums and run the analysis script?

## Proposed Changes
---
### Repository Layout (`/Users/ajoxendine68/Desktop/Xoras_Workspace/galaxy_rotation_reproducibility`)
- **[MODIFY] README.md** – Add detailed repo tree, usage instructions, and citation.
- **[NEW] report.md** – Full reproducibility report with sections:
  - Abstract
  - Hypothesis (Evidence vs. Inference vs. Hypothesis labeling)
  - Software, OS, hardware, random seeds
  - Repository layout tree
  - Data provenance (DOI, version, checksum)
  - Methodology (pre‑processing, model fitting)
  - Results (tables, figures, confidence intervals)
  - Validation tests (unit tests, reproducibility checklist)
  - Limitations & Future work
  - References (full citations with DOIs)
- **[MODIFY] figures/rotation_curve_fit.jpg** – Place generated figure here.
- **[MODIFY] figures/rotation_curve_residuals.jpg** – Place generated figure here.
- **[NEW] checksums.txt** – SHA‑256 hashes for data CSV and both figure files.
- **[NEW] reproducibility_checklist.md** – Checklist for reviewers.
- **[NEW] .github/workflows/ci.yml** – GitHub Actions CI to run `src/preprocess.py` & `src/model_fit.py`, verify checksums, and render the report.
---
### Verification Steps
1. **DOI & Data Verification** – Use `curl` to fetch the DOI landing page, confirm dataset version.
2. **Checksum Generation** – Run `shasum -a 256` on `data/sparc_ngc2403.csv` and both figure files; record in `checksums.txt`.
3. **Path Validation** – Script to ensure every path referenced in `report.md` exists.
4. **CI Run** – Trigger the GitHub Actions workflow locally or via `act`.
5. **Figure Embedding** – Ensure Markdown image links are relative (`![](figures/rotation_curve_fit.jpg)`).

## Verification Plan
### Automated Tests
- `pytest tests/test_checksums.py` – verify recorded hashes.
- `pytest tests/test_paths.py` – ensure referenced files exist.
- `pytest tests/test_report_render.py` – render `report.md` to HTML via `pandoc`.

### Manual Verification
- Open `report.md` in a Markdown viewer.
- Cross‑check each DOI link.
- Run the full analysis pipeline (`python src/preprocess.py && python src/model_fit.py`) and compare generated figures to those embedded.
---
**Next Steps**
- Populate the files listed above.
- Generate SHA‑256 checksums.
- Add CI workflow.
- Run verification steps and update the walkthrough artifact.
