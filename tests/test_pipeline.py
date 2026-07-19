import os
import pytest
import pandas as pd
import numpy as np
from src.preprocess import load_rotation_data
from src.model_fit import fit_rotation_curve, nfw_velocity

def test_load_rotation_data():
    csv_path = "data/sparc_ngc2403.csv"
    assert os.path.exists(csv_path)
    radius, velocity, error = load_rotation_data(csv_path)
    assert len(radius) > 0
    assert len(velocity) == len(radius)
    assert len(error) == len(radius)
    assert radius.dtype == np.float64 or radius.dtype == np.int64

def test_nfw_velocity():
    # Test physical sanity: velocity should be positive for realistic values
    v = nfw_velocity(10.0, 15.0, 0.01)
    assert v > 0
    assert not np.isnan(v)

def test_fit_rotation_curve():
    csv_path = "data/sparc_ngc2403.csv"
    radius, velocity, error = load_rotation_data(csv_path)
    popt, perr, pcov = fit_rotation_curve(radius.values, velocity.values, error.values)
    assert len(popt) == 2
    assert popt[0] > 0  # rs should be positive
    assert popt[1] > 0  # rho0 should be positive
