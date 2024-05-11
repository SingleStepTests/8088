# diff_flags.py

# Display information on flag changes per opcode for a test file.

import json
import sys
import gzip

# Define the flags of the Intel 8088 CPU by their bit positions
FLAGS_8088 = [
    "CF",  # Carry Flag
    "R",   # Reserved, always 1
    "PF",  # Parity Flag
    "R",   # Reserved, always 0
    "AC",  # Auxiliary Carry Flag
    "R",   # Reserved, always 0
    "ZF",  # Zero Flag
    "SF",  # Sign Flag
    "TF",  # Trap Flag
    "IF",  # Interrupt Enable Flag
    "DF",  # Direction Flag
    "OF",  # Overflow Flag
    "R",  # Reserved
    "R",   # Reserved
    "R",   # Reserved
    "R"    # Reserved
]

def compare_flags(initial_flags, final_flags):
    """Compares two flags and returns the names of flags that have changed."""
    initial_flags_bin = format(initial_flags, '016b')
    final_flags_bin = format(final_flags, '016b')
    cleared_flag_names = [FLAGS_8088[i] for i in range(16) if (initial_flags_bin[15-i] != final_flags_bin[15-i]) and (final_flags_bin[15-i] != '1')]
    set_flag_names = [FLAGS_8088[i] for i in range(16) if (initial_flags_bin[15-i] != final_flags_bin[15-i]) and (final_flags_bin[15-i] != '0')]
    unmodified_flags = [FLAGS_8088[i] for i in range(16) if (initial_flags_bin[15-i] == final_flags_bin[15-i]) and (FLAGS_8088[i] != 'R')]
    return (cleared_flag_names, set_flag_names, unmodified_flags)

def process_file(json_filename):

    unmod_dict = {}
    for flag in FLAGS_8088:
        unmod_dict[flag] = True
    unmod_dict["R"] = False
    

    """Reads a JSON file and prints the differences in flag states for each item."""
    open_func = gzip.open if json_filename.endswith('.gz') else open
    with open_func(json_filename, 'rt', encoding='utf-8') as file:
        data = json.load(file)
        
    set_zf = False
       
    for item in data:
        initial_flags = item['initial']['regs']['flags']
        final_flags = item['final']['regs']['flags']
        (cleared_flag_names, set_flag_names, unmodified_flag_names) = compare_flags(initial_flags, final_flags)
        
        print(f"Test: {item['name']} initial: {format(initial_flags, '016b')} final: {format(final_flags, '016b')}")
        print(f"Cleared Flags: {', '.join(cleared_flag_names)}")
        print(f"Set Flags:  {', '.join(set_flag_names)}")
        print(f"Unmodified Flags: {', '.join(unmodified_flag_names)}")
        print(f"AX: {format(item['final']['regs']['ax'], '4x') }\n")
        print(f"DX: {format(item['final']['regs']['dx'], '4x') }\n")
        
        for flag in set_flag_names:
            unmod_dict[flag] = False
        for flag in cleared_flag_names:
            unmod_dict[flag] = False
        
        
        if 'ZF' in set_flag_names:
            print("ZF WAS SET!")
            set_zf = True


    final_unmodified_flags = [key for key, value in unmod_dict.items() if value]
    
    print(f"Globally unmodified flags: {', '.join(final_unmodified_flags)}")
        
        

    if set_zf:
        print("ZF WAS SET!")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 2:
        print("Usage: python diff_flags.py <filename>")
        sys.exit(1)
        
    filename = sys.argv[1]
    process_file(filename)

if __name__ == "__main__":
    main()