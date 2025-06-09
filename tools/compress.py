# gzip all files in a directory.

import os
import sys
import gzip
import shutil

def gzip_files_in_directory(dir_path):
    if not os.path.isdir(dir_path):
        print(f"Error: {dir_path} is not a directory or doesn't exist.")
        return

    for filename in os.listdir(dir_path):

        if filename == "metadata.json" or filename == "readme.md":
            continue

        filepath = os.path.join(dir_path, filename)

        # Skip if it's a directory or already gzipped
        if os.path.isdir(filepath) or filename.endswith('.gz'):
            continue

        gzipped_path = filepath + '.gz'

        with open(filepath, 'rb') as f_in:
            with gzip.open(gzipped_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        print(f"Gzipped {filename} -> {filename}.gz")

def main():
    if len(sys.argv) != 2:
        print("Usage: python gzip_dir.py <directory_path>")
        sys.exit(1)

    directory = sys.argv[1]
    gzip_files_in_directory(directory)

if __name__ == "__main__":
    main()