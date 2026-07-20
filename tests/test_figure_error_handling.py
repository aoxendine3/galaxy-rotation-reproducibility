import os
import pytest
import pandas as pd
import numpy as np
from src.model_fit import generate_plots, perform_fit

def get_dummy_df():
    """Create a minimal DataFrame with valid columns for generate_plots."""
    data = {
        'radius_kpc': np.linspace(0.1, 10, 5),
        'velocity_kms': np.linspace(50, 200, 5),
        'error_kms': np.full(5, 5.0),
        'v_gas': np.full(5, 10.0),
        'v_disk': np.full(5, 20.0),
        'v_bulge': np.full(5, 5.0),
    }
    return pd.DataFrame(data)

def test_generate_plots_permission_error(tmp_path):
    """Attempt to write figures into a directory without write permission."""
    df = get_dummy_df()
    popt, _, _, _, _ = perform_fit(df)
    # Create a subdirectory and remove write permissions
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    os.chmod(readonly_dir, 0o555)  # read & execute only for current user
    fit_path = readonly_dir / "fit.jpg"
    res_path = readonly_dir / "res.jpg"
    with pytest.raises(OSError):
        generate_plots(df, popt, None, None, 0.0, str(fit_path), str(res_path))
    # restore permissions for cleanup
    os.chmod(readonly_dir, 0o755)

def test_generate_plots_nan_data(tmp_path):
    """Provide NaN values in the DataFrame and ensure generate_plots handles them gracefully."""
    df = get_dummy_df()
    df.loc[2, 'v_disk'] = np.nan
    popt, _, _, _, _ = perform_fit(df)
    fit_path = tmp_path / "fit_nan.jpg"
    res_path = tmp_path / "res_nan.jpg"
    with pytest.raises(ValueError):
        generate_plots(df, popt, None, None, 0.0, str(fit_path), str(res_path))

def test_generate_plots_empty_dataframe(tmp_path):
    """Pass an empty DataFrame and verify error handling."""
    df = pd.DataFrame({
        'radius_kpc': [],
        'velocity_kms': [],
        'error_kms': [],
        'v_gas': [],
        'v_disk': [],
        'v_bulge': []
    })
    popt = [10.0, 0.01]
    fit_path = tmp_path / "fit_empty.jpg"
    res_path = tmp_path / "res_empty.jpg"
    with pytest.raises(ValueError):
        generate_plots(df, popt, None, None, 0.0, str(fit_path), str(res_path))
