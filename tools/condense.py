# Condense JSON test files output by combining certain fields into single lines.

import json
import os
import glob
import sys

# Helper function to condense a list into its string representation
def list_to_str(lst):
    def format_value(value):
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

    return '[' + ', '.join(format_value(value) for value in lst) + ']'

# Function to condense JSON data for specific fields
def condense(filename):
    with open(filename, "r") as file:
        data = json.load(file)

    # Iterate over each object in the array
    for idx, item in enumerate(data):
        # Convert the 'bytes' field to a string
        if "bytes" in item:
            item["bytes"] = list_to_str(item["bytes"])

        # Convert each internal list of 'ram' field to a string
        if not isinstance(item.get("initial"), dict):
            print(f"Warning: 'initial' field is not a dict at item index {idx}")       
        else:
            if "ram" in item["initial"]:
                item["initial"]["ram"] = [list_to_str(sublist) for sublist in item["initial"]["ram"]]
            if "queue" in item["initial"]:
                item["initial"]["queue"] = list_to_str(item["initial"]["queue"])
        if not isinstance(item.get("final"), dict):
            print(f"Warning: 'final' field is not a dict at item index {idx}")       
        else:
            if "ram" in item["final"]:
                item["final"]["ram"] = [list_to_str(sublist) for sublist in item["final"]["ram"]]
            if "queue" in item["final"]:
                item["final"]["queue"] = list_to_str(item["final"]["queue"])

        if "cycles" in item:

            for sublist in item["cycles"]:
                try:
                    sublist[1] = int(sublist[1])
                except (ValueError, IndexError, TypeError):
                    pass  # If conversion fails or there's no second element, we skip and leave it unchanged

            item["cycles"] = [list_to_str(sublist) for sublist in item["cycles"]]

    with open(filename, "w") as file:
        def hint_encoder(obj, current_item):
            # If it matches the condense format, it's already a string; return it
            if isinstance(obj, str) and obj.startswith('[') and obj.endswith(']'):
                return obj
            raise TypeError

        results = []
        for current_item in data:
            result_str = json.dumps(current_item, default=lambda obj: hint_encoder(obj, current_item), indent=4)
            
            # Handle 'bytes','ram', and 'cycles' fields
            if "bytes" in current_item:
                result_str = result_str.replace(f'"{current_item["bytes"]}"', current_item["bytes"])
            if "ram" in current_item["initial"]:
                for sublist_str in current_item["initial"]["ram"]:
                    result_str = result_str.replace(f'"{sublist_str}"', sublist_str)
            if "ram" in current_item["final"]:
                for sublist_str in current_item["final"]["ram"]:
                    result_str = result_str.replace(f'"{sublist_str}"', sublist_str)    
            if "queue" in current_item["initial"]:
                result_str = result_str.replace(f'"{current_item["initial"]["queue"]}"', current_item["initial"]["queue"])
            if "queue" in current_item["final"]:
                result_str = result_str.replace(f'"{current_item["final"]["queue"]}"', current_item["final"]["queue"])
            if "cycles" in current_item:
                for sublist_str in current_item["cycles"]:
                    #print(f"sublist str is: {sublist_str}")

                    replace_str = sublist_str.replace('"', '\\"')
                    #print(f"replace str is {replace_str}")
                    result_str = result_str.replace(f'"{replace_str}"', sublist_str)        


            results.append(result_str)

        file.write("[\n" + ",\n".join(results) + "\n]")

def main():
    # Check if folder path is provided
    if len(sys.argv) < 2:
        print("usage: condense.py [path_to_test_dir]")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    # Iterate through each JSON file in the specified folder
    for json_file in glob.glob(os.path.join(folder_path, '*.json')):
        print(f"Condensing file {json_file}...")
        condense(json_file)

if __name__ == '__main__':
    main()

