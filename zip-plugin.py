import os
import zipfile
import time
import hashlib

def zip_plugin():
    """Zips the './physics_export' directory, only adding or updating files that have changed."""

    def get_file_hash(filepath):
        """Compute the MD5 hash of a file for change detection."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            # Read the file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    start_time = time.time()
    zip_filename = 'BlenderPluginSimulation.zip'
    source_dir = './physics_export'
    file_hashes = {}
    hash_filename = 'file_hashes.txt'

    # Load existing file hashes if the zip exists
    if os.path.exists(zip_filename):
        print(f"Zip file '{zip_filename}' exists. Checking for updates.")
        zip_mode = 'a'  # Open in append mode
        if os.path.exists(hash_filename):
            with open(hash_filename, 'r') as f:
                for line in f:
                    filepath, filehash = line.strip().split(',')
                    file_hashes[filepath] = filehash
    else:
        print(f"Creating new zip file '{zip_filename}'.")
        zip_mode = 'w'  # Create new zip

    # Open the zip file and process files
    try:
        with zipfile.ZipFile(zip_filename, zip_mode, zipfile.ZIP_DEFLATED) as zipf:
            new_hashes = {}
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    relative_path = os.path.relpath(filepath, start=source_dir)

                    # Compute the file's hash
                    current_hash = get_file_hash(filepath)
                    new_hashes[relative_path] = current_hash

                    # Check if the file is new or has been modified
                    if relative_path not in file_hashes or file_hashes[relative_path] != current_hash:
                        print(f"Adding/Updating: {relative_path}")
                        zipf.write(filepath, arcname=relative_path)
                    else:
                        print(f"Skipping (unchanged): {relative_path}")

            # Update the hash file with the latest file hashes
            with open(hash_filename, 'w') as f:
                for filepath, filehash in new_hashes.items():
                    f.write(f"{filepath},{filehash}\n")

        total_time = time.time() - start_time
        zip_size = os.path.getsize(zip_filename)
        print(f"Zip file processed in {total_time:.2f} seconds.")
        print(f"Size of the zip file: {zip_size} bytes.")

    except Exception as e:
        print(f"An error occurred during zipping: {e}")
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
        exit(1)

if __name__ == "__main__":
    zip_plugin()
