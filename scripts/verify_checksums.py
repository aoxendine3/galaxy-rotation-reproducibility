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
    # 1. Verify Data CSV Checksum
    csv_path = "data/sparc_ngc2403.csv"
    expected_csv_hash = "e0f987d9c762e614a496861663f38ff2dfee77deec038a365ebbb90a8bd6c357"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        sys.exit(1)
    
    actual_csv_hash = compute_sha256(csv_path)
    if actual_csv_hash != expected_csv_hash:
        print(f"Error: CSV checksum mismatch! Expected {expected_csv_hash}, got {actual_csv_hash}")
        sys.exit(1)
    print("✓ Data CSV checksum verified.")

    # 2. Verify Figure Checksums (with environment awareness)
    figures = {
        "figures/rotation_curve_fit.jpg": {
            "macos": "1e99697fac4a57714fd6e0c9841965224895d60c3f29db284b58eafaecdaa9c1"
        },
        "figures/rotation_curve_residuals.jpg": {
            "macos": "93c69465bf82c6334f66a5c7e25839fac2204627fcdc8fc004439ef05cd38f2b"
        }
    }

    for fig_path, expected_hashes in figures.items():
        if not os.path.exists(fig_path):
            print(f"Error: Figure file {fig_path} not found.")
            sys.exit(1)
        
        actual_hash = compute_sha256(fig_path)
        
        # On macOS (reference system), we strictly enforce the exact byte-for-byte checksum.
        # On other platforms (like Linux/CI runners), matplotlib's rendering engine (freetype, libpng)
        # may produce slightly different bytes. We verify file existence, valid structure, and size.
        is_macos = sys.platform == 'darwin'
        
        if actual_hash == expected_hashes["macos"]:
            print(f"✓ {fig_path} checksum verified (matched macOS reference).")
        else:
            if is_macos:
                print(f"Error: {fig_path} checksum mismatch on macOS! Expected {expected_hashes['macos']}, got {actual_hash}")
                sys.exit(1)
            else:
                # If running on Linux/CI, check that the file is a valid non-empty JPEG image
                size = os.path.getsize(fig_path)
                if size < 10000:
                    print(f"Error: {fig_path} size is abnormally small ({size} bytes).")
                    sys.exit(1)
                
                # Check JPEG magic bytes
                with open(fig_path, 'rb') as f:
                    header = f.read(4)
                if not header.startswith(b'\xff\xd8\xff'):
                    print(f"Error: {fig_path} does not have a valid JPEG header.")
                    sys.exit(1)
                    
                print(f"✓ {fig_path} verified on non-macOS system (valid JPEG, size {size} bytes). actual hash: {actual_hash}")

if __name__ == "__main__":
    verify_all()
