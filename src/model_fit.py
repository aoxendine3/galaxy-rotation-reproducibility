import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from typing import Tuple

# NFW profile for circular velocity
def nfw_velocity(r, rs, rho0):
    # Simplified version: V(r) = sqrt(4 * pi * G * rho0 * rs**3 * (np.log(1 + r/rs) - (r/rs)/(1 + r/rs)) / r)
    G = 4.30091e-6  # kpc * (km/s)^2 / Msun
    term = np.log(1 + r/rs) - (r/rs) / (1 + r/rs)
    return np.sqrt(4 * np.pi * G * rho0 * rs**3 * term / r)

def fit_rotation_curve(radius, velocity, error):
    popt, pcov = curve_fit(nfw_velocity, radius, velocity, sigma=error, absolute_sigma=True, p0=[10.0, 0.01])
    perr = np.sqrt(np.diag(pcov))
    return popt, perr, pcov

if __name__ == "__main__":
    import sys, json
    csv_path = sys.argv[1] if len(sys.argv)>1 else "../data/sparc_ngc2403.csv"
    df = pd.read_csv(csv_path)
    r, v, e = df['radius_kpc'], df['velocity_kms'], df['error_kms']
    popt, perr, _ = fit_rotation_curve(r.values, v.values, e.values)
    result = {
        "rs": popt[0], "rs_err": perr[0],
        "rho0": popt[1], "rho0_err": perr[1]
    }
    print(json.dumps(result, indent=2))
