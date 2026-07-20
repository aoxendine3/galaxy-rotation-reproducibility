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

def validate_cli_args(args):
    """Validate and sanitize command-line arguments.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Parsed command-line arguments.
        
    Raises:
    -------
    ValueError
        If any argument violates physical or mathematical constraints.
    """
    # Validate mass-to-light ratios (must be non-negative for physical meaning)
    if args.upsilon_disk < 0:
        raise ValueError(f"upsilon_disk must be non-negative (got {args.upsilon_disk})")
    if args.upsilon_bulge < 0:
        raise ValueError(f"upsilon_bulge must be non-negative (got {args.upsilon_bulge})")
    
    # Validate initial guess (must be positive)
    if len(args.p0) != 2 or args.p0[0] <= 0 or args.p0[1] <= 0:
        raise ValueError(f"Initial guess p0 must contain two positive values (got {args.p0})")
    
    # Validate fitting bounds (must be [min_rs, min_rho, max_rs, max_rho] with min < max)
    if len(args.bounds) != 4:
        raise ValueError(f"bounds must contain exactly 4 values (got {len(args.bounds)})")
    
    min_rs, min_rho, max_rs, max_rho = args.bounds
    
    if min_rs <= 0 or min_rho <= 0 or max_rs <= 0 or max_rho <= 0:
        raise ValueError(f"All bounds must be positive (got {args.bounds})")
    
    if min_rs >= max_rs:
        raise ValueError(f"rs bounds invalid: min ({min_rs}) >= max ({max_rs})")
    
    if min_rho >= max_rho:
        raise ValueError(f"rho_s bounds invalid: min ({min_rho}) >= max ({max_rho})")
    
    # Validate that initial guess is within bounds
    if not (min_rs <= args.p0[0] <= max_rs):
        raise ValueError(f"Initial rs guess {args.p0[0]} outside bounds [{min_rs}, {max_rs}]")
    
    if not (min_rho <= args.p0[1] <= max_rho):
        raise ValueError(f"Initial rho_s guess {args.p0[1]} outside bounds [{min_rho}, {max_rho}]")

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
    parser.add_argument("--upsilon-disk", type=float, default=0.5, help="Stellar mass-to-light ratio for disk (must be >= 0).")
    parser.add_argument("--upsilon-bulge", type=float, default=0.5, help="Stellar mass-to-light ratio for bulge (must be >= 0).")
    parser.add_argument("--p0", type=float, nargs=2, default=[10.0, 0.01], help="Initial guesses [rs (kpc), rho_s (M_sun/pc^3)].")
    parser.add_argument("--bounds", type=float, nargs=4, default=[0.1, 1e-5, 100.0, 1.0], 
                        help="Fitting bounds: min_rs min_rho_s max_rs max_rho_s (all must be positive; mins < maxs).")
    parser.add_argument("--output-fit", default="figures/rotation_curve_fit.jpg", help="Path to write the fit plot.")
    parser.add_argument("--output-res", default="figures/rotation_curve_residuals.jpg", help="Path to write the residuals plot.")
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    
    # Validate command-line arguments before proceeding
    try:
        validate_cli_args(args)
    except ValueError as e:
        print(f"Error: Invalid argument: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading data file: {args.csv_path}")
    if not os.path.exists(args.csv_path):
        print(f"Error: Data file {args.csv_path} not found.", file=sys.stderr)
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

import sys
import json
import argparse
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import stats

# Configure basic logging (INFO level to stdout)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def validate_cli_args(args):
    """Validate command‑line arguments for physical plausibility.

    Raises
    ------
    ValueError
        If any argument violates constraints expected by the model.
    """
    # Mass‑to‑light ratios must be non‑negative
    if args.upsilon_disk < 0:
        raise ValueError(f"upsilon_disk must be non-negative (got {args.upsilon_disk})")
    if args.upsilon_bulge < 0:
        raise ValueError(f"upsilon_bulge must be non-negative (got {args.upsilon_bulge})")

    # Initial guesses must be two positive values
    if len(args.p0) != 2 or args.p0[0] <= 0 or args.p0[1] <= 0:
        raise ValueError(f"Initial guess p0 must contain two positive values (got {args.p0})")

    # Bounds must be exactly four positive values with min < max
    if len(args.bounds) != 4:
        raise ValueError(f"bounds must contain exactly 4 values (got {len(args.bounds)})")
    min_rs, min_rho, max_rs, max_rho = args.bounds
    if min_rs <= 0 or min_rho <= 0 or max_rs <= 0 or max_rho <= 0:
        raise ValueError(f"All bounds must be positive (got {args.bounds})")
    if min_rs >= max_rs:
        raise ValueError("rs bounds invalid: min >= max")
    if min_rho >= max_rho:
        raise ValueError("rho_s bounds invalid: min >= max")

    # Initial guess must lie within bounds
    if not (min_rs <= args.p0[0] <= max_rs):
        raise ValueError(f"Initial rs guess {args.p0[0]} outside bounds [{min_rs}, {max_rs}]")
    if not (min_rho <= args.p0[1] <= max_rho):
        raise ValueError(f"Initial rho_s guess {args.p0[1]} outside bounds [{min_rho}, {max_rho}]")

# Newtonian gravitational constant G in units of kpc * (km/s)^2 / M_sun.
# Value derived from G = 4.30091e-3 pc * (km/s)^2 / M_sun by multiplying by 1e-3 kpc/pc.
G = 4.30091e-6

# Configure basic logging (INFO level to stdout)
# Duplicate logging config removed

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
    logging.info(f"Initializing fit: p0={p0}, bounds={bounds}")
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
        p0=p0, bounds=bounds, maxfev=5000
    )
    perr = np.sqrt(np.diag(pcov))
    
    # Calculate fitting statistics
    v_fit = fit_func(r, *popt)
    residuals = v_obs - v_fit
    chi2 = np.sum((residuals / err_v) ** 2)
    dof = len(r) - len(popt)
    reduced_chi2 = chi2 / dof

    # Physics validation
    warnings = []
    if reduced_chi2 > 12:
        warnings.append(f"High reduced chi² ({reduced_chi2:.2f}); model may be inadequate.")
    # Normality test on residuals (p-value < 0.05 => non‑normal)
    try:
        stat, p_val = stats.normaltest(residuals)
        if p_val < 0.05:
            warnings.append(f"Residuals fail normality test (p={p_val:.3f}); systematic deviations may exist.")
    except Exception as e:
        warnings.append(f"Residual normality test failed: {e}")

    # Write diagnostics log
    # Determine a deterministic log filename. Prefer the CSV filename if available, otherwise use a generic name.
    # The DataFrame may not have a named index, so we avoid df.iloc[0].name.
    csv_source = getattr(df, 'source_path', None)
    if csv_source:
        base_name = os.path.splitext(os.path.basename(csv_source))[0]
    else:
        base_name = 'fit'
    log_path = f"{base_name}_fit.log"
    log_file = os.path.join('logs', log_path) if os.path.isdir('logs') else os.path.join(os.getcwd(), log_path)
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, 'w') as lf:
        lf.write(f"Fit parameters: rs={popt[0]:.6f}, rho_s={popt[1]:.6f}\n")
        lf.write(f"Parameter uncertainties: rs_err={perr[0]:.6f}, rho_s_err={perr[1]:.6f}\n")
        lf.write(f"Reduced chi²: {reduced_chi2:.4f}\n")
        lf.write(f"Residual normality p‑value: {p_val if 'p_val' in locals() else 'N/A'}\n")
        if warnings:
            lf.write("Warnings:\n")
            for w in warnings:
                lf.write(f"- {w}\n")
        else:
            lf.write("No warnings. Fit looks satisfactory.\n")

    return popt, perr, reduced_chi2, v_fit, residuals

def generate_plots(df, popt, v_fit, residuals, reduced_chi2, output_fit, output_res, upsilon_disk=0.5, upsilon_bulge=0.5):
    logging.info("Generating and saving professional figures...")
    # Defensive checks
    if df.empty:
        raise ValueError("Empty dataframe provided to generate_plots.")
    if df.isnull().any().any():
        raise ValueError("Dataframe contains NaN values; cannot generate plots.")
    r = df['radius_kpc'].values
    logging.info("Generating and saving professional figures...")
    r = df['radius_kpc'].values
    v_obs = df['velocity_kms'].values
    err_v = df['error_kms'].values
    v_gas = df['v_gas'].values
    v_disk = df['v_disk'].values
    v_bulge = df['v_bulge'].values
    # Compute v_fit and residuals if not provided
    if v_fit is None:
        v_fit = fit_model(r, *popt, v_gas, v_disk, v_bulge, upsilon_disk, upsilon_bulge)
    if residuals is None:
        residuals = v_obs - v_fit
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
    parser.add_argument("--upsilon-disk", type=float, default=0.5, help="Stellar mass-to-light ratio for disk (must be >0).")
    parser.add_argument("--upsilon-bulge", type=float, default=0.5, help="Stellar mass-to-light ratio for bulge (must be >=0).")
    parser.add_argument("--p0", type=float, nargs=2, default=[10.0, 0.01], help="Initial guesses [rs, rho_s].")
    parser.add_argument("--bounds", type=float, nargs=4, default=[0.1, 1e-5, 100.0, 1.0],
                        help="Fitting bounds: min_rs min_rho_s max_rs max_rho_s.")
    parser.add_argument("--output-fit", default="figures/rotation_curve_fit.jpg", help="Path to write the fit plot.")
    parser.add_argument("--output-res", default="figures/rotation_curve_residuals.jpg", help="Path to write the residuals plot.")
    parser.add_argument("--version", action="version", version="galaxy_rotation_reproducibility 1.0")
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    
    logging.info(f"Loading data file: {args.csv_path}")
    if not os.path.exists(args.csv_path):
        logging.error(f"Data file {args.csv_path} not found.")
        sys.exit(1)
        
    df = pd.read_csv(args.csv_path)
    
        # Validate CLI arguments using central helper
    try:
        validate_cli_args(args)
    except ValueError as e:
        logging.error(str(e))
        sys.exit(1)
    
    bounds_tuple = ([args.bounds[0], args.bounds[1]], [args.bounds[2], args.bounds[3]])
    
    logging.info("Performing NFW non-linear least-squares optimization...")
    popt, perr, reduced_chi2, v_fit, residuals = perform_fit(
        df,
        upsilon_disk=args.upsilon_disk,
        upsilon_bulge=args.upsilon_bulge,
        p0=args.p0,
        bounds=bounds_tuple
    )
    fit_warnings = []  # No warnings returned from perform_fit

    
    result = {
        "rs_kpc": round(popt[0], 4),
        "rs_err_kpc": round(perr[0], 5),
        "rho_s_msun_pc3": round(popt[1], 6),
        "rho_s_err_msun_pc3": round(perr[1], 7),
        "reduced_chi2": round(reduced_chi2, 4)
    }
    
    # Output warnings if any
    if fit_warnings:
        for w in fit_warnings:
            logging.warning(w)
    
    logging.info("--- Fit Convergence Reached ---")
    logging.info(json.dumps(result, indent=2))
    logging.info("--------------------------------")
    
    generate_plots(
        df, popt, v_fit, residuals, reduced_chi2, 
        args.output_fit, args.output_res,
        upsilon_disk=args.upsilon_disk,
        upsilon_bulge=args.upsilon_bulge
    )
    
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
