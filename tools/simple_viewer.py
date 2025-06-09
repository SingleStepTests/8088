# View a test in a more human-readable format
import json
import argparse
import sys
import gzip

def format_hex_16(val):
    return f"{val:04X}"

def format_hex_8(val):
    return f"{val:02X}"

def format_reg(name, val):
    return f"    {name:<5} = {format_hex_16(val)} ({val})"

def print_test(test, idx):
    name = test.get("name", "")
    bytes_arr = test.get("bytes", [])
    bytes_len = len(bytes_arr)

    print(f"======== Test #{idx if idx >= 0 else '???'} ========")
    print(f'Name: "{name}"')
    hex_bytes = " ".join(format_hex_8(b) for b in bytes_arr)
    print(f"Bytes ({bytes_len}): [ {hex_bytes} ]")

    initial = test.get("initial", {})
    regs = initial.get("regs", {})
    ram = initial.get("ram", [])
    queue = initial.get("queue", [])

    print("Initial CPU State:")
    print("  Registers:")
    reg_order = [
        "ax","bx","cx","dx","cs","ss","ds","es","sp","bp","si","di","ip","flags"
    ]
    for r in reg_order:
        if r in regs:
            print(format_reg(r, regs[r]))

    print(f"  RAM entries: {len(ram)}")
    for addr_val in ram:
        if len(addr_val) == 2:
            addr, val = addr_val
            print(f"    {format_hex_16(addr)} = {format_hex_8(val)} ({val})")
        else:
            print(f"    Invalid RAM entry: {addr_val}")

    print(f"  Queue length: {len(queue)}")
    queue_hex = " ".join(format_hex_8(b) for b in queue)
    print(f"  Queue bytes: [ {queue_hex} ]")

    final = test.get("final", {})
    regs = final.get("regs", {})
    ram = final.get("ram", [])
    queue = final.get("queue", [])

    print("Final CPU State:")
    print("  Registers:")
    for r in reg_order:
        if r in regs:
            print(format_reg(r, regs[r]))

    print(f"  RAM entries: {len(ram)}")
    for addr_val in ram:
        if len(addr_val) == 2:
            addr, val = addr_val
            print(f"    {format_hex_16(addr)} = {format_hex_8(val)} ({val})")
        else:
            print(f"    Invalid RAM entry: {addr_val}")

    print(f"  Queue length: {len(queue)}")
    queue_hex = " ".join(format_hex_8(b) for b in queue)
    print(f"  Queue bytes: [ {queue_hex} ]")

    cycles = test.get("cycles", [])
    print(f"Cycles count: {len(cycles)}")

    print("")
    print("  Cyc ALE Addr  Seg Mem Io  BHE Data Bus   T  Q Qb")
    print("  --- --- ----- --- --- --- --- ---- ----  -- - --")

    for i, cycle in enumerate(cycles):
        if len(cycle) < 11:
            cycle = list(cycle) + [""] * (11 - len(cycle))
        pin = cycle[0]
        addr = cycle[1]
        seg = cycle[2]
        mem = cycle[3]
        io = cycle[4]
        bhe = cycle[5]
        data = cycle[6]
        bus = cycle[7]
        t = cycle[8]
        qop = cycle[9]
        qb = cycle[10]

        if pin & 1 == 1:
            ale_str = "A:"
        else:
            ale_str = "  "

        # Conditional data width formatting
        if bus == "PASV" and (mem != "---" or io != "---"):
            if data < 256:
                data_str = f"{data:02X}"
            else:
                data_str = f"{data:04X}"
        else:
            data_str = "----"

        addr_str = f"{addr:05X}"
        pin_str = f"{pin:3}"
        i_str = f"{i:3}"

        if qop != '-':
            qb_str = f"{qb:02X}"
        else: 
            qb_str = '--'

        print(f"  {i_str} {ale_str:>3} {addr_str}  {seg} {mem} {io} {bhe: >3} {data_str:>4} {bus: <4}  {t: <2} {qop} {qb_str: >2}")

    hash_val = test.get("hash", None)
    if hash_val:
        print(f"Hash: {hash_val}")

def load_json_file(filename):
    if filename.endswith(".gz"):
        with gzip.open(filename, "rt", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="View JSON CPU test file.")
    parser.add_argument("--file", required=True, help="JSON or JSON.GZ test file path")
    parser.add_argument("--index", type=int, required=True, help="Index of test to display")
    args = parser.parse_args()

    tests = load_json_file(args.file)

    if not isinstance(tests, list):
        print(f"Error: JSON root is not a list")
        sys.exit(1)

    if args.index < 0 or args.index >= len(tests):
        print(f"Error: index {args.index} out of range (0..{len(tests)-1})")
        sys.exit(1)

    print_test(tests[args.index], args.index)

if __name__ == "__main__":
    main()