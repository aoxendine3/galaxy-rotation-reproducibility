import urllib.request
import os

def download_sparc_data():
    url = "https://raw.githubusercontent.com/carsondowns-cte/Rotmod_LTG/master/NGC2403_rotmod.dat"
    target_dir = "data"
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, "sparc_ngc2403.csv")
    
    print(f"Downloading SPARC data for NGC 2403 from {url}...")
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error downloading data: {e}")
        raise
    
    lines = content.split('\n')
    output_lines = ["radius_kpc,velocity_kms,error_kms,v_gas,v_disk,v_bulge"]
    
    records_count = 0
    last_radius = -1.0
    
    for line_idx, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) >= 6:
            try:
                # Validate that the parsed parts are actual numbers
                radius = float(parts[0])
                vobs = float(parts[1])
                errv = float(parts[2])
                vgas = float(parts[3])
                vdisk = float(parts[4])
                vbul = float(parts[5])
                
                # Check data constraints
                if radius <= 0 or vobs <= 0 or errv <= 0:
                    raise ValueError(f"Negative or zero value found at line {line_idx}: {line}")
                if radius <= last_radius:
                    raise ValueError(f"Radius is not strictly increasing at line {line_idx}: {radius} <= {last_radius}")
                
                last_radius = radius
                records_count += 1
                output_lines.append(f"{radius:.2f},{vobs:.2f},{errv:.2f},{vgas:.2f},{vdisk:.2f},{vbul:.2f}")
            except ValueError as e:
                print(f"Schema validation error: {e}")
                raise
                
    # Validate expected row count for NGC 2403
    expected_rows = 73
    if records_count != expected_rows:
        raise ValueError(f"Integrity check failed: Expected {expected_rows} data points, but parsed {records_count}.")
        
    with open(target_path, 'w') as f:
        f.write('\n'.join(output_lines) + '\n')
        
    print(f"Data saved successfully to {target_path} ({records_count} records).")

if __name__ == "__main__":
    download_sparc_data()
