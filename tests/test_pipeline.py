import os
import hashlib
import urllib.request
import numpy as np
import pandas as pd
import pytest
from src.preprocess import load_rotation_data
from src.model_fit import perform_fit, nfw_velocity, generate_plots

# Calculate canonical project root folder path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_repo_path(relative_path):
    return os.path.join(PROJECT_ROOT, relative_path)

def compute_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def test_data_integrity():
    csv_path = get_repo_path("data/sparc_ngc2403.csv")
    assert os.path.exists(csv_path), f"Raw data file is missing at {csv_path}!"
    expected_hash = "e0f987d9c762e614a496861663f38ff2dfee77deec038a365ebbb90a8bd6c357"
    actual_hash = compute_sha256(csv_path)
    assert actual_hash == expected_hash, f"CSV hash mismatch! Expected {expected_hash}, got {actual_hash}"

def test_load_rotation_data():
    csv_path = get_repo_path("data/sparc_ngc2403.csv")
    radius, velocity, error = load_rotation_data(csv_path)
    assert len(radius) == 73, f"Expected 73 data points, got {len(radius)}"
    assert len(velocity) == 73
    assert len(error) == 73
    assert np.all(radius > 0)
    assert np.all(velocity > 0)
    assert np.all(error > 0)

def test_nfw_velocity_math():
    # Test NFW profile physical consistency: v circular must be positive, real, and non-zero
    v = nfw_velocity(10.0, 15.0, 0.01)
    assert v > 0
    assert not np.isnan(v)
    
    # Test clipping doesn't break at near-zero radii
    v_zero = nfw_velocity(1e-9, 15.0, 0.01)
    assert v_zero > 0
    assert not np.isnan(v_zero)

def test_fit_rotation_curve_precision():
    csv_path = get_repo_path("data/sparc_ngc2403.csv")
    df = pd.read_csv(csv_path)
    popt, perr, reduced_chi2, v_fit, residuals = perform_fit(df)
    
    # Tightened regression thresholds (assert precision matches deterministic outputs)
    assert np.isclose(popt[0], 11.055063839279198, rtol=1e-5), f"rs drifted: {popt[0]}"
    assert np.isclose(popt[1], 0.01004214197502815, rtol=1e-5), f"rho_s drifted: {popt[1]}"
    assert np.isclose(reduced_chi2, 10.012547439178881, rtol=1e-5), f"reduced chi2 drifted: {reduced_chi2}"
    
    assert len(v_fit) == 73
    assert len(residuals) == 73

def test_figure_generation_and_existence(tmp_path):
    csv_path = get_repo_path("data/sparc_ngc2403.csv")
    df = pd.read_csv(csv_path)
    popt, perr, reduced_chi2, v_fit, residuals = perform_fit(df)
    
    # Save plots to temp path during testing to verify generate_plots completes successfully
    fit_temp_path = os.path.join(tmp_path, "rotation_curve_fit.jpg")
    res_temp_path = os.path.join(tmp_path, "rotation_curve_residuals.jpg")
    
    generate_plots(df, popt, v_fit, residuals, reduced_chi2, fit_temp_path, res_temp_path)
    
    assert os.path.exists(fit_temp_path), "Temp fit plot was not written!"
    assert os.path.exists(res_temp_path), "Temp residuals plot was not written!"
    assert os.path.getsize(fit_temp_path) > 10000, "Temp fit plot is empty or too small!"
    assert os.path.getsize(res_temp_path) > 10000, "Temp residuals plot is empty or too small!"

def test_doi_resolution():
    doi_url = "https://doi.org/10.3847/0004-6256/152/6/157"
    req = urllib.request.Request(
        doi_url, 
        method='HEAD',
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            assert status in [200, 301, 302], f"DOI returned unexpected status code: {status}"
    except Exception as e:
        # Fallback to GET if HEAD method is blocked by the server
        try:
            req.method = 'GET'
            with urllib.request.urlopen(req, timeout=10) as response:
                status = response.status
                assert status in [200, 301, 302], f"DOI returned unexpected status code on GET: {status}"
        except Exception as err:
            pytest.fail(f"DOI failed to resolve: {err}")
