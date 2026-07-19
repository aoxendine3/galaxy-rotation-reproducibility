import pandas as pd
from typing import Tuple

def load_rotation_data(csv_path: str) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Load rotation curve data.
    Returns radius (kpc), velocity (km/s), and velocity error (km/s).
    """
    df = pd.read_csv(csv_path)
    return df['radius_kpc'], df['velocity_kms'], df['error_kms']

if __name__ == "__main__":
    import sys
    r, v, e = load_rotation_data(sys.argv[1])
    print(r.head())
    print(v.head())
    print(e.head())
