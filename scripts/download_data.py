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
    
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
    
    lines = content.split('\n')
    output_lines = ["radius_kpc,velocity_kms,error_kms,v_gas,v_disk,v_bulge"]
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) >= 6:
            # Columns: Rad Vobs errV Vgas Vdisk Vbul
            radius = parts[0]
            vobs = parts[1]
            errv = parts[2]
            vgas = parts[3]
            vdisk = parts[4]
            vbul = parts[5]
            output_lines.append(f"{radius},{vobs},{errv},{vgas},{vdisk},{vbul}")
            
    with open(target_path, 'w') as f:
        f.write('\n'.join(output_lines) + '\n')
        
    print(f"Data saved successfully to {target_path} ({len(output_lines) - 1} records).")

if __name__ == "__main__":
    download_sparc_data()
