import os
import hashlib
import numpy as np
import pandas as pd
import pytest
from src.preprocess import load_rotation_data
from src.model_fit import perform_fit, nfw_velocity

def compute_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def test_data_integrity():
    csv_path = "data/sparc_ngc2403.csv"
    assert os.path.exists(csv_path), "Raw data file is missing!"
    expected_hash = "e0f987d9c762e614a496861663f38ff2dfee77deec038a365ebbb90a8bd6c357"
    actual_hash = compute_sha256(csv_path)
    assert actual_hash == expected_hash, f"CSV hash mismatch! Expected {expected_hash}, got {actual_hash}"

def test_load_rotation_data():
    csv_path = "data/sparc_ngc2403.csv"
    radius, velocity, error = load_rotation_data(csv_path)
    assert len(radius) == 73, f"Expected 73 data points, got {len(radius)}"
    assert len(velocity) == 73
    assert len(error) == 73
    assert np.all(radius > 0)
    assert np.all(velocity > 0)

def test_nfw_velocity():
    # Test physical sanity: circular velocity should be positive and non-zero
    v = nfw_velocity(10.0, 15.0, 0.01)
    assert v > 0
    assert not np.isnan(v)

def test_fit_rotation_curve():
    csv_path = "data/sparc_ngc2403.csv"
    df = pd.read_csv(csv_path)
    popt, perr, reduced_chi2, v_fit, residuals = perform_fit(df)
    
    # Assert parameters converge close to expectations
    assert np.isclose(popt[0], 11.055, atol=1e-2), f"rs mismatch: {popt[0]}"
    assert np.isclose(popt[1], 0.010, atol=1e-3), f"rho_s mismatch: {popt[1]}"
    assert np.isclose(reduced_chi2, 10.01, atol=1e-2), f"reduced chi2 mismatch: {reduced_chi2}"
    
    assert len(v_fit) == 73
    assert len(residuals) == 73

def test_figures_exist():
    # Ensure the fit and residuals plots exist and are non-empty
    fit_path = "figures/rotation_curve_fit.jpg"
    res_path = "figures/rotation_curve_residuals.jpg"
    assert os.path.exists(fit_path), "Fit plot is missing!"
    assert os.path.exists(res_path), "Residuals plot is missing!"
    assert os.path.getsize(fit_path) > 10000, "Fit plot is empty or too small!"
    assert os.path.getsize(res_path) > 10000, "Residuals plot is empty or too small!"
