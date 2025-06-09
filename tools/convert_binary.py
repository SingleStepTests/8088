# Convert CPU tests from JSON to binary MOO format.

import os
import gzip
import json
import struct
import binascii
import sys

# Register name LUT
REG_ORDER = [
    'ax', 'bx', 'cx', 'dx',
    'cs', 'ss', 'ds', 'es',
    'sp', 'bp', 'si', 'di',
    'ip', 'flags'
]

# ASCII Chunk IDs strings
CHUNK_MOO  = b'MOO '
CHUNK_TEST = b'TEST'
CHUNK_NAME = b'NAME'
CHUNK_BYTS = b'BYTS'
CHUNK_INIT = b'INIT'
CHUNK_FINA = b'FINA'
CHUNK_REGS = b'REGS'
CHUNK_RAM  = b'RAM '
CHUNK_QUEU = b'QUEU'
CHUNK_CYCL = b'CYCL'
CHUNK_HASH = b'HASH'

# Segment name LUT
SEGMENT_MAP = {
    "ES": 0,
    "SS": 1,
    "CS": 2,
    "DS": 3,
    "--": 4,
}

# Bus status LUT
BUS_STATUS_MAP = {
    "INTA": 0,
    "IOR": 1,
    "IOW": 2,
    "MEMR": 3,
    "MEMW": 4,
    "HALT": 5,
    "CODE": 6,
    "PASV": 7,
}

# CPU T-cycle LUT
T_STATE_MAP = {
    "Ti": 0,
    "T1": 1,
    "T2": 2,
    "T3": 3,
    "T4": 4,
}

# CPU Queue operation LUT
QUEUE_OP_MAP = {
    "-": 0,
    "F": 1,
    "E": 2,
    "S": 3,
}

def encode_3char_bitfield(s):
    s = s.ljust(3, '-')[:3]
    bitfield = 0
    for i, ch in enumerate(s):
        bit = 1 if ch != '-' else 0
        bitfield |= (bit << (2 - i))
    return bitfield

def encode_cycle(c):
    pin_bitfield = c[0]
    address_latch = c[1]
    segment_status = SEGMENT_MAP.get(c[2], 4)
    memory_status = encode_3char_bitfield(c[3])
    io_status = encode_3char_bitfield(c[4])
    bhe_status = c[5]
    data_bus = c[6]
    bus_status = BUS_STATUS_MAP.get(c[7], 7)
    t_state = T_STATE_MAP.get(c[8], 0)
    queue_op_status = QUEUE_OP_MAP.get(c[9], 0)
    queue_byte_read = c[10]

    return struct.pack('<B I B B B B H B B B B',
                       pin_bitfield,
                       address_latch,
                       segment_status,
                       memory_status,
                       io_status,
                       bhe_status,
                       data_bus,
                       bus_status,
                       t_state,
                       queue_op_status,
                       queue_byte_read)

def encode_cycles(cycles_list):
    data = struct.pack('<I', len(cycles_list))
    for c in cycles_list:
        data += encode_cycle(c)
    return data

def encode_regs(regs_dict):
    bitmask = 0
    values = []
    for i, r in enumerate(REG_ORDER):
        if r in regs_dict:
            bitmask |= (1 << i)
            values.append(regs_dict[r])
    data = struct.pack('<H', bitmask)  # 16-bit bitmask
    if values:
        data += struct.pack('<' + 'H'*len(values), *values)
    return data

def encode_ram(ram_list):
    entries = []
    for addr, val in ram_list:
        entries.append(struct.pack('<IB', addr, val))
    return b''.join(entries)

def encode_queue(queue_list):
    return bytes(queue_list)

def encode_regs_chunk(regs_dict):
    data = encode_regs(regs_dict)
    return data

def encode_ram_chunk(ram_list):
    data = struct.pack('<I', len(ram_list))
    data += encode_ram(ram_list)
    return data

def encode_queue_chunk(queue_list):
    data = struct.pack('<I', len(queue_list))
    data += encode_queue(queue_list)
    return data

def encode_cpu_state_chunk(label, state_dict):
    chunks = b''
    regs_data = encode_regs_chunk(state_dict.get('regs', {}))
    chunks += CHUNK_REGS + struct.pack('<I', len(regs_data)) + regs_data

    ram_data = encode_ram_chunk(state_dict.get('ram', []))
    chunks += CHUNK_RAM + struct.pack('<I', len(ram_data)) + ram_data

    queue_data = encode_queue_chunk(state_dict.get('queue', []))
    chunks += CHUNK_QUEU + struct.pack('<I', len(queue_data)) + queue_data

    return label.encode('ascii') + struct.pack('<I', len(chunks)) + chunks

def encode_name_chunk(name_str):
    encoded = name_str.encode('utf-8')
    return struct.pack('<I', len(encoded)) + encoded

def encode_bytes_chunk(bytes_list):
    return struct.pack('<I', len(bytes_list)) + bytes(bytes_list)

def encode_hash_chunk(hash_str):
    return binascii.unhexlify(hash_str)

def write_moo_chunk(f, version, test_count, cpu_name):
    # cpu_name: ASCII string exactly 4 chars (pad with spaces if needed)
    if len(cpu_name) > 4:
        raise ValueError(f"CPU name '{cpu_name}' exceeds 4 characters")
    cpu_name_padded = cpu_name.ljust(4, ' ').encode('ascii')

    data = struct.pack('<II4s', version, test_count, cpu_name_padded)
    f.write(CHUNK_MOO)
    f.write(struct.pack('<I', len(data)))
    f.write(data)

def process_test(test):
    # Prepend the test index as a 4-byte unsigned int at the start of TEST chunk data
    idx = test.get('idx', 0)
    inner_chunks = b''

    name_data = encode_name_chunk(test['name'])
    inner_chunks += CHUNK_NAME + struct.pack('<I', len(name_data)) + name_data

    byts_data = encode_bytes_chunk(test.get('bytes', []))
    inner_chunks += CHUNK_BYTS + struct.pack('<I', len(byts_data)) + byts_data

    init_data = encode_cpu_state_chunk('INIT', test['initial'])
    inner_chunks += init_data

    fina_data = encode_cpu_state_chunk('FINA', test['final'])
    inner_chunks += fina_data

    cycles_data = encode_cycles(test.get('cycles', []))
    inner_chunks += CHUNK_CYCL + struct.pack('<I', len(cycles_data)) + cycles_data

    if 'hash' in test:
        hash_data = encode_hash_chunk(test['hash'])
        inner_chunks += CHUNK_HASH + struct.pack('<I', len(hash_data)) + hash_data

    # Prepend index as 4-byte uint
    idx_bytes = struct.pack('<I', idx)
    test_data = idx_bytes + inner_chunks

    return CHUNK_TEST + struct.pack('<I', len(test_data)) + test_data

def process_file(input_path, output_path, cpu_name):
    print(f'Reading {input_path}...')
    with gzip.open(input_path, 'rt', encoding='utf-8') as f:
        data = json.load(f)

    print(f'Encoding {len(data)} tests into binary...')
    with open(output_path, 'wb') as fout:
        write_moo_chunk(fout, version=1, test_count=len(data), cpu_name=cpu_name)
        for test in data:
            bin_data = process_test(test)
            fout.write(bin_data)
    print(f'Wrote output to {output_path}')

def main():
    if len(sys.argv) != 4:
        print(f'Usage: {sys.argv[0]} <input_directory> <cpu_name_4chars> <output_directory>')
        exit(1)

    input_directory = sys.argv[1]
    cpu_name = sys.argv[2]
    output_directory = sys.argv[3]

    if len(cpu_name) > 4:
        print(f'Error: CPU name "{cpu_name}" must be at most 4 characters')
        exit(1)

    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    for fname in sorted(os.listdir(input_directory)):
        if not fname.endswith('.json.gz'):
            continue
        input_path = os.path.join(input_directory, fname)
        base_name = os.path.splitext(os.path.splitext(fname)[0])[0]
        output_fname = base_name + '.MOO'
        output_path = os.path.join(output_directory, output_fname)
        process_file(input_path, output_path, cpu_name)

if __name__ == '__main__':
    main()