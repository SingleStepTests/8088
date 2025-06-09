# subset.py
# 
# This utility is designed to generate a subset of a test suite.
# Given a percentage, source and destination paths, all JSON and JSON.gz files
# in the source directory will be parsed and the specified percentage of tests 
# exported to the same filename in the destination directory.
#
# For example, if you have a test suite that contains 10,000 tests for each 
# opcode, issuing:
#
# subset.py --percent 10 D:\bigtests D:\smalltests
#
# will generate a test suite in D:\smalltests containing 1,000 tests for each 
# opcode.
#
# subset.py --limit 100 D:\bigtests D:\smalltests
#
# will generate a test suite in D:\smalltests containing 100 tests for each 
# opcode.
#
# Rationale: It may be desirable to operate on a smaller test suite for speed,
# for example, to validate tests on a commit hook or other CI task.
import json
import os
import gzip
import sys
import shutil
import argparse

def get_files_in_directory(path):
    for filename in os.listdir(path):
        if filename.endswith('.json') or filename.endswith('.json.gz'):
            yield os.path.join(path, filename)

def load_json_file(filename):
    if filename.endswith('.json'):
        with open(filename, 'r') as f:
            return json.load(f)
    elif filename.endswith('.json.gz'):
        with gzip.open(filename, 'rt') as f:
            return json.load(f)

def save_json_file(filename, data):
    if filename.endswith('.json'):
        with open(filename, 'w') as f:
            json.dump(data, f)
    elif filename.endswith('.json.gz'):
        with gzip.open(filename, 'wt') as f:
            json.dump(data, f)

def filter_percentage(data, percentage):
    num_items = int(len(data) * percentage / 100)
    return data[:num_items]

def filter_limit(data, limit):
    return data[:limit]

def main():
    parser = argparse.ArgumentParser(description="Subset JSON test files by percentage or fixed limit.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--percent', type=float, help='Keep approximately this percentage of tests (0-100).')
    group.add_argument('--limit', type=int, help='Keep exactly this many tests.')

    parser.add_argument('source_path', help='Directory containing input JSON or JSON.GZ files.')
    parser.add_argument('destination_path', help='Directory to save filtered files.')

    args = parser.parse_args()

    if not os.path.exists(args.destination_path):
        os.makedirs(args.destination_path)

    for source_file in get_files_in_directory(args.source_path):
        data = load_json_file(source_file)

        if not isinstance(data, list):
            print(f"Copying file {source_file} unchanged as it does not contain a JSON array.")
            shutil.copy(source_file, os.path.join(args.destination_path, os.path.basename(source_file)))
            continue

        if args.percent is not None:
            if not (0 <= args.percent <= 100):
                print(f"Error: --percent must be between 0 and 100. Got {args.percent}")
                sys.exit(1)
            filtered_data = filter_percentage(data, args.percent)
        else:
            if args.limit < 0:
                print(f"Error: --limit must be non-negative. Got {args.limit}")
                sys.exit(1)
            filtered_data = filter_limit(data, args.limit)

        dest_file = os.path.join(args.destination_path, os.path.basename(source_file))
        save_json_file(dest_file, filtered_data)

if __name__ == "__main__":
    main()