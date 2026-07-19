import pandas as pd
from typing import Tuple

def load_rotation_data(csv_path: str) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Load rotation curve data and perform validation checks.
    Returns radius (kpc), velocity (km/s), and velocity error (km/s).
    """
    df = pd.read_csv(csv_path)
    
    # Assert expected columns are present
    required_cols = ['radius_kpc', 'velocity_kms', 'error_kms']
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Missing required column in rotation data: {col}")
            
    # Check data constraints
    if df.empty:
        raise ValueError("Rotation data file is empty.")
    if (df['radius_kpc'] <= 0).any() or (df['velocity_kms'] <= 0).any() or (df['error_kms'] <= 0).any():
        raise ValueError("Data contains non-positive values (negative or zero).")
        
    # Check monotonicity
    if not df['radius_kpc'].is_monotonic_increasing:
        raise ValueError("Radius values are not strictly increasing.")
        
    return df['radius_kpc'], df['velocity_kms'], df['error_kms']

if __name__ == "__main__":
    import sys
    r, v, e = load_rotation_data(sys.argv[1])
    print(r.head())
    print(v.head())
    print(e.head())
