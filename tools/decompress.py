# decompress all gzipped files in a directory 

import os
import sys
import gzip
import shutil

def ungzip_files_in_directory(dir_path):
    if not os.path.isdir(dir_path):
        print(f"Error: {dir_path} is not a directory or doesn't exist.")
        return

    for filename in os.listdir(dir_path):
        if not filename.endswith('.gz'):
            continue

        gzipped_path = os.path.join(dir_path, filename)
        original_path = os.path.join(dir_path, filename[:-3])  # Remove '.gz'

        with gzip.open(gzipped_path, 'rb') as f_in:
            with open(original_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        print(f"Un-gzipped {filename} -> {filename[:-3]}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python ungzip_dir.py <directory_path>")
        sys.exit(1)

    directory = sys.argv[1]
    ungzip_files_in_directory(directory)

if __name__ == "__main__":
    main()