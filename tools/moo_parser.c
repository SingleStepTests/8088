// Example parser for the MOO CPU test format.
// You will need to decompress gzipped test files before reading them.

// (C) 2025 Daniel Balsom 

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define MAX_NAME_LEN 256

const char* REG_LUT[] = {
    "ax", "bx", "cx", "dx",
    "cs", "ss", "ds", "es",
    "sp", "bp", "si", "di",
    "ip", "flags"
};
#define REG_COUNT (sizeof(REG_LUT) / sizeof(REG_LUT[0]))

// Represent a readable buffer of memory
typedef struct {
    const uint8_t* data;
    size_t size;
    size_t pos;
} MemStream;

int memstream_read(MemStream* s, void* buf, size_t len) {
    if (s->pos + len > s->size) {
        return 0;
    }
    memcpy(buf, s->data + s->pos, len);
    s->pos += len;
    return 1;
}

int memstream_read_u32_le(MemStream* s, uint32_t* out) {
    uint8_t buf[4];
    if (!memstream_read(s, buf, 4)) {
        return 0;
    }
    *out = buf[0] | (buf[1] << 8) | (buf[2] << 16) | (buf[3] << 24);
    return 1;
}

int memstream_read_chunk(MemStream* s, char* out_type, uint32_t* out_len, const uint8_t** out_data) {
    if (s->pos + 8 > s->size) {
        return 0;
    }
    memcpy(out_type, s->data + s->pos, 4);
    out_type[4] = 0;
    s->pos += 4;
    if (!memstream_read_u32_le(s, out_len)) {
        return 0;
    }
    if (s->pos + *out_len > s->size) {
        return 0;
    }
    *out_data = s->data + s->pos;
    s->pos += *out_len;
    return 1;
}

uint16_t read_u16_le(const uint8_t* p) {
    return p[0] | (p[1] << 8);
}

// Display the register state (initial or final state)
void print_regs(const uint8_t* data, uint32_t len) {
    if (len < 2) {
        printf("  (Invalid regs length %u)\n", len);
        return;
    }
    uint16_t bitmask = data[0] | (data[1] << 8);
    const uint8_t* p = data + 2;
    uint32_t remaining = len - 2;

    printf("  Registers:\n");
    for (int i = 0; i < REG_COUNT; i++) {
        if ((bitmask >> i) & 1) {
            if (remaining < 2) {
                printf("    (Unexpected end of data for register %s)\n", REG_LUT[i]);
                return;
            }
            uint16_t val = p[0] | (p[1] << 8);
            printf("    %-5s = %04X (%u)\n", REG_LUT[i], val, val);
            p += 2;
            remaining -= 2;
        }
    }
    if (remaining > 0) {
        printf("  (Warning: %u extra bytes in regs chunk)\n", remaining);
    }
}

// Display the memory contents (initial or final state)
void print_ram(const uint8_t* data, uint32_t len) {
    if (len < 4) {
        printf("  RAM chunk too short (%u bytes)\n", len);
        return;
    }
    uint32_t count = data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24);
    if (count == 0) {
        printf("  RAM entries: 0 (empty)\n");
        return;
    }
    if (len < 4 + count * 5) {
        printf("  RAM chunk length mismatch: expected at least %u bytes but got %u\n", 4 + count * 5, len);
        return;
    }
    printf("  RAM entries: %u\n", count);
    const uint8_t* p = data + 4;
    for (uint32_t i = 0; i < count; i++) {
        uint32_t addr = p[0] | (p[1] << 8) | (p[2] << 16) | (p[3] << 24);
        uint8_t val = p[4];
        printf("    %05X = %02X (%u)\n", addr, val, val);
        p += 5;
        if (i >= 1000) {
            printf("    ... (truncated)\n");
            break;
        }
    }
}

// Display the instruction queue contents
void print_queue(const uint8_t* data, uint32_t len) {
    if (len < 4) {
        printf("  Queue chunk too short\n");
        return;
    }
    uint32_t count = data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24);
    printf("  Queue length: %u\n", count);
    if (len < 4 + count) {
        printf("  Queue chunk length mismatch\n");
        return;
    }
    const uint8_t* p = data + 4;
    printf("  Queue bytes: [ ");
    for (uint32_t i = 0; i < count; i++) {
        printf("%02X ", p[i]);
        if (i >= 31) {
            printf("... ");
            break;
        }
    }
    printf("]\n");
}

// Display the instruction name
void print_name(const uint8_t* data, uint32_t len) {
    if (len < 4) {
        printf("  Name chunk too short\n");
        return;
    }
    uint32_t slen = data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24);
    if (len < 4 + slen) {
        printf("  Name chunk length mismatch\n");
        return;
    }
    char namebuf[MAX_NAME_LEN + 1];
    uint32_t tocopy = slen > MAX_NAME_LEN ? MAX_NAME_LEN : slen;
    memcpy(namebuf, data + 4, tocopy);
    namebuf[tocopy] = '\0';
    printf("Name: \"%s\"\n", namebuf);
}

// Display raw bytes
void print_bytes(const uint8_t* data, uint32_t len) {
    if (len < 4) {
        printf("  Bytes chunk too short\n");
        return;
    }
    uint32_t count = data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24);
    printf("Bytes (%u): [ ", count);
    if (len < 4 + count) {
        printf("chunk length mismatch\n");
        return;
    }
    const uint8_t* p = data + 4;
    for (uint32_t i = 0; i < count; i++) {
        printf("%02X ", p[i]);
    }
    printf("]\n");
}

// Display the SHA1 hash chunk
void print_hash(const uint8_t* data, uint32_t len) {
    if (len != 20) {
        printf("  Hash chunk length unexpected (%u)\n", len);
        return;
    }
    printf("Hash: ");
    for (int i = 0; i < 20; i++) {
        printf("%02X", data[i]);
    }
    printf("\n");
}

// Print a table of the CPU cycles array from a CYCL chunk
void print_cycles(const uint8_t* data, uint32_t len) {

    static const char* SEGMENT_STRS[] = { "ES", "SS", "CS", "DS", "--" };
    static const char* BUS_STATUS_STRS[] = { "INTA", "IOR", "IOW", "MEMR", "MEMW", "HALT", "CODE", "PASV" };
    static const char* T_STATE_STRS[] = { "Ti", "T1", "T2", "T3", "T4" };
    static const char* QUEUE_OP_STRS[] = { "-", "F", "E", "S" };
    static const char MEM_IO_LETTERS[3] = { 'R','A','W' };

    if (len < 4) {
        printf("  Cycles chunk too short\n");
        return;
    }

    uint32_t count = data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24);
    printf("Cycles count: %u\n", count);
    if (len < 4 + count * 11) {
        printf("  Cycles chunk length mismatch\n");
        return;
    }

    const uint8_t* p = data + 4;

    printf("%5s %3s %5s %3s %3s %3s %3s %2s %7s %4s %4s %2s\n",
        "Idx", "Pin", "Addr", "Seg", "Mem", "Io", "BHE",
        "Data", "Bus", "T", "Qop", "Qb");
    printf("%5s %3s %5s %3s %3s %3s %3s %2s %7s %4s %4s %2s\n",
        "---", "---", "-----", "---", "---", "---", "---",
        "----", "----", "--", "---", "--");

    for (uint32_t i = 0; i < count; i++) {
        uint8_t pin_bitfield = p[0];
        uint32_t address_latch = p[1] | (p[2] << 8) | (p[3] << 16) | (p[4] << 24);
        uint8_t segment_status = p[5];
        uint8_t memory_status = p[6];
        uint8_t io_status = p[7];
        uint8_t bhe_status = p[8];
        uint16_t data_bus = p[9] | (p[10] << 8);
        uint8_t bus_status = p[11];
        uint8_t t_state = p[12];
        uint8_t queue_op_status = p[13];
        uint8_t queue_byte_read = p[14];

        char mem_str[4], io_str[4];
        for (int b = 0; b < 3; b++) {
            mem_str[b] = (memory_status & (1 << (2 - b))) ? MEM_IO_LETTERS[b] : '-';
            io_str[b] = (io_status & (1 << (2 - b))) ? MEM_IO_LETTERS[b] : '-';
        }
        mem_str[3] = io_str[3] = 0;

        printf("%5u %03X %05X %3s %3s %3s %3X %4.02X %7s %4s %4s %02X\n",
            i,
            pin_bitfield,
            address_latch,
            segment_status < 5 ? SEGMENT_STRS[segment_status] : "?",
            mem_str,
            io_str,
            bhe_status,
            data_bus,
            bus_status < 8 ? BUS_STATUS_STRS[bus_status] : "?",
            t_state < 5 ? T_STATE_STRS[t_state] : "?",
            queue_op_status < 4 ? QUEUE_OP_STRS[queue_op_status] : "?",
            queue_byte_read
        );

        p += 15;
    }
}

// Print a CPU state. This may be an initial or final state.
void print_cpu_state(const uint8_t* data, uint32_t len, const char* label) {
    printf("%s CPU State:\n", label);

    const uint8_t* end = data + len;
    const uint8_t* p = data;

    while (p + 8 <= end) {
        char chunk_type[5];
        memcpy(chunk_type, p, 4);
        chunk_type[4] = 0;
        p += 4;
        uint32_t chunk_len = p[0] | (p[1] << 8) | (p[2] << 16) | (p[3] << 24);
        p += 4;
        if (p + chunk_len > end) {
            printf("  %s chunk length exceeds bounds\n", chunk_type);
            break;
        }
        if (strcmp(chunk_type, "REGS") == 0) {
            print_regs(p, chunk_len);
        }
        else if (strcmp(chunk_type, "RAM ") == 0) {
            print_ram(p, chunk_len);
        }
        else if (strcmp(chunk_type, "QUEU") == 0) {
            print_queue(p, chunk_len);
        }
        else {
            printf("  Unknown subchunk '%s'\n", chunk_type);
        }
        p += chunk_len;
    }
}

// Parse an integer argument from the commandline
int parse_uint_arg(const char* arg, const char* prefix, int* out_val) {
    size_t len = strlen(prefix);
    if (strncmp(arg, prefix, len) == 0) {
        char* endptr;
        long val = strtol(arg + len, &endptr, 10);
        if (*endptr == '\0' && val >= 0) {
            *out_val = (int)val;
            return 1;
        }
    }
    return 0;
}

int main(int argc, char** argv) {
    int limit = -1;   // no limit
    int index = -1;   // no index filter
    const char* filename = NULL;

    // Parse command line args
    for (int i = 1; i < argc; i++) {
        if (parse_uint_arg(argv[i], "-limit=", &limit)) {
            continue;
        }
        else if (parse_uint_arg(argv[i], "-index=", &index)) {
            continue;
        }
        else if (filename == NULL) {
            filename = argv[i];
        }
        else {
            fprintf(stderr, "Unexpected argument: %s\n", argv[i]);
            return 1;
        }
    }

    if (filename == NULL) {
        fprintf(stderr, "Usage: %s [-limit=N] [-index=N] <binary_test_file>\n", argv[0]);
        return 1;
    }

    FILE* f = fopen(filename, "rb");
    if (!f) {
        perror("Error opening file");
        return 1;
    }

    // Read the entire file into memory for speed
    fseek(f, 0, SEEK_END);
    size_t filesize = ftell(f);
    fseek(f, 0, SEEK_SET);

    uint8_t* buffer = malloc(filesize);
    if (!buffer) {
        fprintf(stderr, "Out of memory\n");
        fclose(f);
        return 1;
    }

    if (fread(buffer, 1, filesize, f) != filesize) {
        fprintf(stderr, "Error reading file\n");
        free(buffer);
        fclose(f);
        return 1;
    }
    fclose(f);

    MemStream stream = { buffer, filesize, 0 };
    int test_count = 0;

    // Loop through file, parsing chunks
    while (1) {
        char chunk_type[5];
        uint32_t chunk_len;
        const uint8_t* chunk_data;

        if (!memstream_read_chunk(&stream, chunk_type, &chunk_len, &chunk_data)) break;

        if (strcmp(chunk_type, "MOO ") == 0) {
            if (chunk_len != 12) {
                printf("Invalid MOO chunk length: expected 12, got %u\n", chunk_len);
            }
            else {
                uint32_t version = chunk_data[0] | (chunk_data[1] << 8) | (chunk_data[2] << 16) | (chunk_data[3] << 24);
                uint32_t test_count = chunk_data[4] | (chunk_data[5] << 8) | (chunk_data[6] << 16) | (chunk_data[7] << 24);
                char cpu_name[5] = { 0 };
                memcpy(cpu_name, chunk_data + 8, 4);
                // Trim trailing spaces
                for (int i = 3; i >= 0; i--) {
                    if (cpu_name[i] == ' ') cpu_name[i] = '\0';
                    else break;
                }
                printf("File MOO Chunk:\n  Version: %u\n  Test Count: %u\n  CPU type: %s\n",
                    version, test_count, cpu_name);
            }
            // Continue reading next chunk
            continue; 
        }

        if (strcmp(chunk_type, "TEST") == 0) {
            if (index >= 0 && test_count != index) {
                test_count++;
                continue;
            }

            uint32_t test_idx = chunk_data[0] | (chunk_data[1] << 8) | (chunk_data[2] << 16) | (chunk_data[3] << 24);
            printf("\n==== Test #%u (%u bytes) ====\n", test_idx, chunk_len);
            const uint8_t* p = chunk_data + 4; // skip index field
            const uint8_t* end = chunk_data + chunk_len;

            while (p + 8 <= end) {
                char subchunk_type[5];
                memcpy(subchunk_type, p, 4);
                subchunk_type[4] = 0;
                p += 4;

                if (p + 4 > end) break;
                uint32_t subchunk_len = p[0] | (p[1] << 8) | (p[2] << 16) | (p[3] << 24);
                p += 4;

                if (subchunk_len == 0) {
                    printf("  Warning: zero-length subchunk '%s', stopping to avoid infinite loop\n", subchunk_type);
                    break;
                }

                if (p + subchunk_len > end) break;

                if (strcmp(subchunk_type, "NAME") == 0) {
                    print_name(p, subchunk_len);
                }
                else if (strcmp(subchunk_type, "BYTS") == 0) {
                    print_bytes(p, subchunk_len);
                }
                else if (strcmp(subchunk_type, "INIT") == 0) {
                    print_cpu_state(p, subchunk_len, "Initial");
                }
                else if (strcmp(subchunk_type, "FINA") == 0) {
                    print_cpu_state(p, subchunk_len, "Final");
                }
                else if (strcmp(subchunk_type, "CYCL") == 0) {
                    print_cycles(p, subchunk_len);
                }
                else if (strcmp(subchunk_type, "HASH") == 0) {
                    print_hash(p, subchunk_len);
                }
                else {
                    printf("  Unknown subchunk '%s' (%u bytes)\n", subchunk_type, subchunk_len);
                }
                p += subchunk_len;
            }

            test_count++;

            // Stop if we reached specified limit
            if (limit >= 0 && test_count >= limit) {
                break;
            }
            // Stop if we reached specified index
            if (index >= 0 && test_count > index) {
                break;
            }
        }
        else {
            printf("Unknown top-level chunk '%s' (%u bytes), skipping\n", chunk_type, chunk_len);
        }
    }

    free(buffer);
    return 0;
}