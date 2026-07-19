import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# G in units of kpc * (km/s)^2 / M_sun
G = 4.30091e-6

def nfw_velocity(r, rs, rho_s):
    """Calculate the circular velocity of a spherical NFW halo at radius r."""
    # Ensure positive physical parameters
    rs = np.abs(rs)
    rho_s = np.abs(rho_s)
    # Convert rho_s from M_sun/pc^3 to M_sun/kpc^3 for unit consistency (1 kpc = 1000 pc)
    rho_s_kpc = rho_s * 1e9
    x = r / rs
    # Avoid division by zero at r=0
    x = np.maximum(x, 1e-5)
    term = np.log(1 + x) - x / (1 + x)
    # V_NFW^2 = 4 * pi * G * rho_s * rs^3 * (ln(1+x) - x/(1+x)) / r
    v_nfw_sq = 4 * np.pi * G * rho_s_kpc * (rs ** 3) * term / r
    return np.sqrt(v_nfw_sq)

def fit_model(r, rs, rho_s, v_gas, v_disk, upsilon_disk=0.5):
    """Calculate model velocity combining gas, disk (scaled by mass-to-light ratio), and NFW dark matter."""
    v_nfw = nfw_velocity(r, rs, rho_s)
    # v_model = sqrt(v_gas^2 + upsilon_disk * v_disk^2 + v_nfw^2)
    v_model_sq = v_gas**2 + upsilon_disk * v_disk**2 + v_nfw**2
    return np.sqrt(np.maximum(v_model_sq, 0.0))

def perform_fit(df):
    r = df['radius_kpc'].values
    v_obs = df['velocity_kms'].values
    err_v = df['error_kms'].values
    v_gas = df['v_gas'].values
    v_disk = df['v_disk'].values
    
    # We fit only the NFW halo parameters rs and rho_s, assuming upsilon_disk = 0.5
    # Define wrapper function for curve_fit
    def fit_func(r_data, rs, rho_s):
        return fit_model(r_data, rs, rho_s, v_gas, v_disk, upsilon_disk=0.5)
    
    # Initial guess: rs = 10.0 kpc, rho_s = 0.01 M_sun/pc^3
    # Bounds: rs in [0.1, 100.0], rho_s in [1e-5, 1.0]
    popt, pcov = curve_fit(
        fit_func, r, v_obs, sigma=err_v, absolute_sigma=True,
        p0=[10.0, 0.01], bounds=([0.1, 1e-5], [100.0, 1.0])
    )
    perr = np.sqrt(np.diag(pcov))
    
    # Calculate chi-squared
    v_fit = fit_func(r, *popt)
    residuals = v_obs - v_fit
    chi2 = np.sum((residuals / err_v) ** 2)
    dof = len(r) - len(popt)
    reduced_chi2 = chi2 / dof
    
    return popt, perr, reduced_chi2, v_fit, residuals

def generate_plots(df, popt, v_fit, residuals, output_fit, output_res):
    r = df['radius_kpc'].values
    v_obs = df['velocity_kms'].values
    err_v = df['error_kms'].values
    v_gas = df['v_gas'].values
    v_disk = df['v_disk'].values
    
    rs, rho_s = popt
    v_nfw = nfw_velocity(r, rs, rho_s)
    v_bar = np.sqrt(v_gas**2 + 0.5 * v_disk**2)
    
    # Use professional styling
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 14,
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'figure.titlesize': 16
    })
    
    # 1. Fit Plot
    plt.figure(figsize=(9, 6))
    plt.errorbar(r, v_obs, yerr=err_v, fmt='ko', mfc='none', label='Observed (SPARC)', capsize=3)
    plt.plot(r, v_fit, 'r-', linewidth=2, label=f'Best Fit (reduced $\\chi^2 = {reduced_chi2:.2f}$)')
    plt.plot(r, v_nfw, 'b--', label='NFW Dark Matter Halo')
    plt.plot(r, v_bar, 'g:', label='Baryonic components (Gas + Disk)')
    plt.plot(r, v_gas, 'c-.', alpha=0.5, label='Gas component')
    plt.plot(r, np.sqrt(0.5)*v_disk, 'm-.', alpha=0.5, label=r'Disk component ($\Upsilon_*=0.5$)')
    
    plt.xlabel('Radius (kpc)')
    plt.ylabel('Velocity (km/s)')
    plt.title('NGC 2403 Rotation Curve & NFW Model Fit')
    plt.legend(loc='lower right', frameon=True)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_fit), exist_ok=True)
    plt.savefig(output_fit, dpi=300)
    plt.close()
    
    # 2. Residuals Plot
    plt.figure(figsize=(9, 4))
    plt.errorbar(r, residuals, yerr=err_v, fmt='ko', mfc='none', capsize=3)
    plt.axhline(0, color='r', linestyle='--', linewidth=1.5)
    plt.xlabel('Radius (kpc)')
    plt.ylabel('Residual (O - C) (km/s)')
    plt.title('Fit Residuals for NGC 2403')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_res, dpi=300)
    plt.close()
    
    print(f"Figures saved successfully to {output_fit} and {output_res}")

if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/sparc_ngc2403.csv"
    if not os.path.exists(csv_path):
        print(f"Error: Data file {csv_path} not found.")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    popt, perr, reduced_chi2, v_fit, residuals = perform_fit(df)
    
    result = {
        "rs_kpc": round(popt[0], 2),
        "rs_err_kpc": round(perr[0], 3),
        "rho_s_msun_pc3": round(popt[1], 4),
        "rho_s_err_msun_pc3": round(perr[1], 5),
        "reduced_chi2": round(reduced_chi2, 2)
    }
    
    print("Fit Results:")
    print(json.dumps(result, indent=2))
    
    # Generate the plots
    fit_path = "figures/rotation_curve_fit.jpg"
    res_path = "figures/rotation_curve_residuals.jpg"
    generate_plots(df, popt, v_fit, residuals, fit_path, res_path)
