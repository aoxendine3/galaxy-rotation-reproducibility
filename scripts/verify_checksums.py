import os
import hashlib
import sys

def compute_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def verify_all():
    # 1. Parse and verify data/checksums.txt for all listed files
    checksums_file = "data/checksums.txt"
    if not os.path.exists(checksums_file):
        print(f"Error: Checksums reference file {checksums_file} not found.")
        sys.exit(1)
        
    print(f"Verifying source files against {checksums_file}...")
    with open(checksums_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) != 2:
                print(f"Error: Invalid line format in {checksums_file}: {line}")
                sys.exit(1)
            
            expected_hash, filepath = parts
            if not os.path.exists(filepath):
                print(f"Error: Tracked file {filepath} not found.")
                sys.exit(1)
                
            actual_hash = compute_sha256(filepath)
            if actual_hash != expected_hash:
                print(f"Error: Checksum mismatch for {filepath}! Expected {expected_hash}, got {actual_hash}")
                sys.exit(1)
            print(f"✓ {filepath} checksum matches.")

    # 2. Verify Figure Existence and Formats (derived files)
    figures = [
        "figures/rotation_curve_fit.jpg",
        "figures/rotation_curve_residuals.jpg"
    ]

    print("\nVerifying generated figures (derived files)...")
    for fig_path in figures:
        if not os.path.exists(fig_path):
            print(f"Error: Expected figure {fig_path} is missing from output directory.")
            sys.exit(1)
            
        size = os.path.getsize(fig_path)
        if size < 10000:
            print(f"Error: Generated figure {fig_path} size is abnormally small ({size} bytes).")
            sys.exit(1)
            
        # Verify valid JPEG header (magic numbers FF D8 FF)
        with open(fig_path, 'rb') as f:
            header = f.read(4)
        if not header.startswith(b'\xff\xd8\xff'):
            print(f"Error: Generated figure {fig_path} is not a valid JPEG image (invalid magic bytes).")
            sys.exit(1)
            
        print(f"✓ {fig_path} generated successfully (valid JPEG, size {size} bytes).")

    print("\nAll integrity checks completed successfully.")

if __name__ == "__main__":
    verify_all()
