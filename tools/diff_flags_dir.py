# diff_flags_dir.py

# Display information on flag changes per opcode for an entire directory of tests.

import json
import sys
import io
import gzip
from pathlib import Path
import copy

# Define the flags of the Intel 8088 CPU by their bit positions
FLAGS_8088 = [
    "c",  # Carry Flag
    "R",   # Reserved, always 1
    "p",  # Parity Flag
    "R",   # Reserved, always 0
    "a",  # Auxiliary Carry Flag
    "R",   # Reserved, always 0
    "z",  # Zero Flag
    "s",  # Sign Flag
    "t",  # Trap Flag
    "i",  # Interrupt Enable Flag
    "d",  # Direction Flag
    "o",  # Overflow Flag
    "R",  # Reserved
    "R",   # Reserved
    "R",   # Reserved
    "R"    # Reserved
]

FLAGS_SHORT = [
    "o", "d", "i", "s", "z", "a", "p", "c" 
]    

def make_flag_str(flag_list):
    
    flag_str = ""
    for flag in FLAGS_SHORT:
        if flag in flag_list:
            flag_str += flag
        else:
            flag_str += "."
            
    return flag_str
        
def call_silently(function, silence=True, *args, **kwargs):
    if silence:
        # Save the current stdout so we can restore it later
        original_stdout = sys.stdout
        # Create a dummy file object to redirect the output to
        sys.stdout = io.StringIO()
        # Call the function with any arguments, capturing any printed output
        result = function(*args, **kwargs)
        # Restore the original stdout
        sys.stdout = original_stdout
        # Return the function's result if needed
        return result
    else:
        # Call the function normally without silencing
        return function(*args, **kwargs)
        
def compare_flags(initial_flags, final_flags):
    """Compares two flags and returns the names of flags that have changed."""
    initial_flags_bin = format(initial_flags, '016b')
    final_flags_bin = format(final_flags, '016b')
    cleared_flag_names = [FLAGS_8088[i] for i in range(16) if (initial_flags_bin[15-i] != final_flags_bin[15-i]) and (final_flags_bin[15-i] != '1')]
    set_flag_names = [FLAGS_8088[i] for i in range(16) if (initial_flags_bin[15-i] != final_flags_bin[15-i]) and (final_flags_bin[15-i] != '0')]
    unmodified_flags = [FLAGS_8088[i] for i in range(16) if (initial_flags_bin[15-i] == final_flags_bin[15-i]) and (FLAGS_8088[i] != 'R')]
    return (cleared_flag_names, set_flag_names, unmodified_flags)

def get_flags(final_flags):
    flag_states = {}
    final_flags_bin = format(final_flags, '016b')
    for i in range(16):
        flag_states[FLAGS_8088[i]] = final_flags_bin[15-i]

    return flag_states

def process_file(json_filename):

    mod_dict = {}
    set_dict = {}
    cleared_dict = {}
    always_set_dict = {}
    always_cleared_dict = {}
    
    for flag in FLAGS_8088:
        set_dict[flag] = False
        cleared_dict[flag] = False
        mod_dict[flag] = False
        always_set_dict[flag] = True
        always_cleared_dict[flag] = True
        
        
    set_dict["R"] = False
    cleared_dict["R"] = False
    always_set_dict["R"] = False
    always_cleared_dict["R"] = False
    mod_dict["R"] = False
    
    """Reads a JSON file and prints the differences in flag states for each item."""
    open_func = gzip.open if json_filename.endswith('.gz') else open
    with open_func(json_filename, 'rt', encoding='utf-8') as file:
        data = json.load(file)
        
    if not isinstance(data, list):
        print(f"Error: The file {json_filename} does not contain a JSON array.")
        return (False, [], [], [], [], [])
        
    for item in data:
        initial_flags = item['initial']['regs']['flags']
        final_flags = item['final']['regs']['flags']
        final_flag_states = get_flags(final_flags)
        (cleared_flag_names, set_flag_names, unmodified_flag_names) = compare_flags(initial_flags, final_flags)
        
        print(f"Test: {item['name']} initial: {format(initial_flags, '016b')} final: {format(final_flags, '016b')}")
        print(f"final flag states: {final_flag_states}")
        print(f"Cleared Flags: {', '.join(cleared_flag_names)}")
        print(f"Set Flags:  {', '.join(set_flag_names)}")
        print(f"Unmodified Flags: {', '.join(unmodified_flag_names)}")
        print(f"AX: {format(item['final']['regs']['ax'], '4x') }\n")
        
        for flag in set_flag_names:
            set_dict[flag] = True
            mod_dict[flag] = True
            
        for flag in cleared_flag_names:
            cleared_dict[flag] = True
            mod_dict[flag] = True
        
        for flag in FLAGS_8088:
            if final_flag_states[flag] == '0':
                always_set_dict[flag] = False
            if final_flag_states[flag] == '1':
                always_cleared_dict[flag] = False
                
        print(f"Always set dict: {always_set_dict}")                    
        print(f"Always cleared dict: {always_cleared_dict}")
                
    final_set_flags = [key for key, value in set_dict.items() if value]
    final_cleared_flags = [key for key, value in cleared_dict.items() if value]
    final_modified_flags = [key for key, value in mod_dict.items() if value]
    
    always_set_flags = [key for key, value in always_set_dict.items() if value]
    always_set_flags = [flag for flag in always_set_flags if flag in final_modified_flags]

    always_cleared_flags = [key for key, value in always_cleared_dict.items() if value]
    always_cleared_flags = [flag for flag in always_cleared_flags if flag in final_modified_flags]
   
    return (True, final_set_flags, final_cleared_flags, final_modified_flags, always_set_flags, always_cleared_flags)
        
        
def process_directory(directory_path):
    """Processes each JSON and gzipped JSON file in the given directory."""
    # List all files in the given directory
    path = Path(directory_path)
    for file_path in path.iterdir():
        if file_path.is_file() and file_path.suffix in ['.json', '.gz']:
             (result, final_set_flags, final_cleared_flags, final_modified_flags, always_set_flags, always_cleared_flags) = call_silently(process_file, True, str(file_path))
             
             if result:
                print(f"{file_path.name}: set: {make_flag_str(final_set_flags)} cleared: {make_flag_str(final_cleared_flags)} modified: {make_flag_str(final_modified_flags)} always_set: {make_flag_str(always_set_flags)} always_cleared: {make_flag_str(always_cleared_flags)}")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 2:
        print("Usage: python diff_flags_dir.py <directory_path>")
        sys.exit(1)
        
    process_directory(sys.argv[1])

if __name__ == "__main__":
    main()