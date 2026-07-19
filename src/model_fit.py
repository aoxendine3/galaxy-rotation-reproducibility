import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Newtonian gravitational constant G in units of kpc * (km/s)^2 / M_sun.
# Value derived from G = 4.30091e-3 pc * (km/s)^2 / M_sun by multiplying by 1e-3 kpc/pc.
G = 4.30091e-6

def nfw_velocity(r, rs, rho_s):
    """Calculate the circular velocity of a spherical Navarro-Frenk-White (NFW) dark matter halo at radius r.
    
    Parameters:
    -----------
    r : float or numpy array
        Radius from the galaxy center in kpc.
    rs : float
        Scale radius of the NFW halo in kpc.
    rho_s : float
        Characteristic density of the NFW halo in M_sun/pc^3.
        
    Returns:
    --------
    v_nfw : float or numpy array
        Circular velocity in km/s.
    """
    # Ensure physical parameters remain strictly positive during curve fitting exploration
    rs = np.abs(rs)
    rho_s = np.abs(rho_s)
    
    # Unit Conversion: convert rho_s from M_sun/pc^3 to M_sun/kpc^3.
    # Since 1 kpc = 1000 pc, 1 pc^-3 = (10^-3 kpc)^-3 = 10^9 kpc^-3.
    # Therefore, rho_s_kpc = rho_s * 1e9.
    rho_s_kpc = rho_s * 1e9
    
    x = r / rs
    
    # Clipping near-zero radii to avoid division by zero or NaN at r=0.
    # Choosing 1e-5 kpc (~0.01 pc) preserves numerical stability without impacting physical curves 
    # since observed astronomical data points are always at much larger radii (r > 0.1 kpc).
    x = np.maximum(x, 1e-5)
    
    term = np.log(1 + x) - x / (1 + x)
    
    # V_NFW^2 = 4 * pi * G * rho_s_kpc * rs^3 * [ln(1+x) - x/(1+x)] / r
    v_nfw_sq = 4 * np.pi * G * rho_s_kpc * (rs ** 3) * term / r
    return np.sqrt(v_nfw_sq)

def fit_model(r, rs, rho_s, v_gas, v_disk, v_bulge, upsilon_disk=0.5, upsilon_bulge=0.5):
    """Calculate the total model circular velocity.
    
    Combines the baryonic components (gas, disk, and bulge) and the dark matter halo:
    V_model = sqrt( V_gas^2 + upsilon_disk * V_disk^2 + upsilon_bulge * V_bulge^2 + V_NFW^2 )
    
    Parameters:
    -----------
    r : numpy array
        Radii in kpc.
    rs, rho_s : float
        NFW halo parameters.
    v_gas, v_disk, v_bulge : numpy arrays
        Component velocities in km/s.
    upsilon_disk : float
        Stellar mass-to-light ratio for the disk.
    upsilon_bulge : float
        Stellar mass-to-light ratio for the bulge.
    """
    v_nfw = nfw_velocity(r, rs, rho_s)
    v_model_sq = (v_gas ** 2) + (upsilon_disk * (v_disk ** 2)) + (upsilon_bulge * (v_bulge ** 2)) + (v_nfw ** 2)
    return np.sqrt(np.maximum(v_model_sq, 0.0))

def perform_fit(df, upsilon_disk=0.5, upsilon_bulge=0.5, p0=[10.0, 0.01], bounds=([0.1, 1e-5], [100.0, 1.0])):
    print(f"Initializing fit: p0={p0}, bounds={bounds}")
    r = df['radius_kpc'].values
    v_obs = df['velocity_kms'].values
    err_v = df['error_kms'].values
    v_gas = df['v_gas'].values
    v_disk = df['v_disk'].values
    v_bulge = df['v_bulge'].values
    
    # Wrapper function for curve_fit incorporating the baryonic profiles
    def fit_func(r_data, rs, rho_s):
        return fit_model(r_data, rs, rho_s, v_gas, v_disk, v_bulge, upsilon_disk, upsilon_bulge)
    
    popt, pcov = curve_fit(
        fit_func, r, v_obs, sigma=err_v, absolute_sigma=True,
        p0=p0, bounds=bounds
    )
    perr = np.sqrt(np.diag(pcov))
    
    # Calculate fitting statistics
    v_fit = fit_func(r, *popt)
    residuals = v_obs - v_fit
    chi2 = np.sum((residuals / err_v) ** 2)
    dof = len(r) - len(popt)
    reduced_chi2 = chi2 / dof
    
    return popt, perr, reduced_chi2, v_fit, residuals

def generate_plots(df, popt, v_fit, residuals, reduced_chi2, output_fit, output_res, upsilon_disk=0.5, upsilon_bulge=0.5):
    print("Generating and saving professional figures...")
    r = df['radius_kpc'].values
    v_obs = df['velocity_kms'].values
    err_v = df['error_kms'].values
    v_gas = df['v_gas'].values
    v_disk = df['v_disk'].values
    v_bulge = df['v_bulge'].values
    
    rs, rho_s = popt
    v_nfw = nfw_velocity(r, rs, rho_s)
    # Baryonic sum
    v_bar = np.sqrt(v_gas**2 + upsilon_disk * v_disk**2 + upsilon_bulge * v_bulge**2)
    
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 14,
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'figure.titlesize': 16
    })
    
    # Figure 1: Rotation Curve Fit
    plt.figure(figsize=(9, 6))
    plt.errorbar(r, v_obs, yerr=err_v, fmt='ko', mfc='none', label='Observed (SPARC)', capsize=3)
    plt.plot(r, v_fit, 'r-', linewidth=2, label=f'Best Fit (reduced $\\chi^2 = {reduced_chi2:.2f}$)')
    plt.plot(r, v_nfw, 'b--', label='NFW Dark Matter Halo')
    plt.plot(r, v_bar, 'g:', label='Total Baryonic components')
    plt.plot(r, v_gas, 'c-.', alpha=0.5, label='Gas component')
    plt.plot(r, np.sqrt(upsilon_disk)*v_disk, 'm-.', alpha=0.5, label=f'Disk component ($\\Upsilon_*^d={upsilon_disk}$)')
    if np.any(v_bulge > 0):
        plt.plot(r, np.sqrt(upsilon_bulge)*v_bulge, 'y-.', alpha=0.5, label=f'Bulge component ($\\Upsilon_*^b={upsilon_bulge}$)')
        
    plt.xlabel('Radius (kpc)')
    plt.ylabel('Velocity (km/s)')
    plt.title('NGC 2403 Rotation Curve & NFW Model Fit')
    plt.legend(loc='lower right', frameon=True)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(os.path.abspath(output_fit)), exist_ok=True)
    plt.savefig(output_fit, dpi=300)
    plt.close()
    
    # Figure 2: Fit Residuals
    plt.figure(figsize=(9, 4))
    plt.errorbar(r, residuals, yerr=err_v, fmt='ko', mfc='none', capsize=3)
    plt.axhline(0, color='r', linestyle='--', linewidth=1.5)
    plt.xlabel('Radius (kpc)')
    plt.ylabel('Residual (O - C) (km/s)')
    plt.title('Fit Residuals for NGC 2403')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(os.path.abspath(output_res)), exist_ok=True)
    plt.savefig(output_res, dpi=300)
    plt.close()
    
    print(f"Figures written successfully:\n  - Fit: {output_fit}\n  - Residuals: {output_res}")

def build_parser():
    parser = argparse.ArgumentParser(description="Fit an NFW dark matter halo to galaxy rotation curves.")
    parser.add_argument("csv_path", nargs="?", default="data/sparc_ngc2403.csv", help="Path to raw SPARC data CSV.")
    parser.add_argument("--upsilon-disk", type=float, default=0.5, help="Stellar mass-to-light ratio for disk.")
    parser.add_argument("--upsilon-bulge", type=float, default=0.5, help="Stellar mass-to-light ratio for bulge.")
    parser.add_argument("--p0", type=float, nargs=2, default=[10.0, 0.01], help="Initial guesses [rs, rho_s].")
    parser.add_argument("--bounds", type=float, nargs=4, default=[0.1, 1e-5, 100.0, 1.0], 
                        help="Fitting bounds: min_rs min_rho_s max_rs max_rho_s.")
    parser.add_argument("--output-fit", default="figures/rotation_curve_fit.jpg", help="Path to write the fit plot.")
    parser.add_argument("--output-res", default="figures/rotation_curve_residuals.jpg", help="Path to write the residuals plot.")
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    
    print(f"Loading data file: {args.csv_path}")
    if not os.path.exists(args.csv_path):
        print(f"Error: Data file {args.csv_path} not found.")
        sys.exit(1)
        
    df = pd.read_csv(args.csv_path)
    
    bounds_tuple = ([args.bounds[0], args.bounds[1]], [args.bounds[2], args.bounds[3]])
    
    print("Performing NFW non-linear least-squares optimization...")
    popt, perr, reduced_chi2, v_fit, residuals = perform_fit(
        df, 
        upsilon_disk=args.upsilon_disk, 
        upsilon_bulge=args.upsilon_bulge, 
        p0=args.p0, 
        bounds=bounds_tuple
    )
    
    result = {
        "rs_kpc": round(popt[0], 4),
        "rs_err_kpc": round(perr[0], 5),
        "rho_s_msun_pc3": round(popt[1], 6),
        "rho_s_err_msun_pc3": round(perr[1], 7),
        "reduced_chi2": round(reduced_chi2, 4)
    }
    
    print("\n--- Fit Convergence Reached ---")
    print(json.dumps(result, indent=2))
    print("--------------------------------\n")
    
    generate_plots(
        df, popt, v_fit, residuals, reduced_chi2, 
        args.output_fit, args.output_res,
        upsilon_disk=args.upsilon_disk,
        upsilon_bulge=args.upsilon_bulge
    )

if __name__ == "__main__":
    main()
