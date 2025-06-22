
# MOO File Format Specification, Version 1

This document describes the structure of the **MOO** test file format used by CPU tests for the 8088, 8086, V20 and V30 CPUs.
**MOO** stands for Machine Opcode Operation file.

All fields are little-endian.

## File Overview

A **MOO** file consists of a **MOO** chunk, followed by one or more **TEST** chunks concatenated together.

Each chunk has the following structure:

| Field       | Size (bytes) | Description                              |
|-------------|--------------|------------------------------------------|
| Chunk Type  | 4            | ASCII string identifying chunk type (e.g. `TEST`, `NAME`, etc.) |
| Chunk Length| 4            | uint32 size of chunk data |
| Chunk Data  | Variable     | Chunk payload bytes as described below  |

## File-header Chunk: `MOO `

| Field       | Size (bytes) | Description                              |
|-------------|--------------|------------------------------------------|
| Chunk Type  | 4            | File ID `MOO ` (note the trailing space) |
| Chunk Length| 4            | uint32 size of chunk data |
| Version     | 1            | uint32 File Version       |
| Reserved    | 3            | 3 bytes reserved          |
| Test Count  | 4            | uint32 Number of tests in file |
| CPU Name    | 4            | ASCII ID of CPU being tested, padded with spaces |
---

The `MOO ` header is at least 12 bytes as of file version 1, but may grow in future versions. 
The current version of `MOO ` is version 1. Additional chunk types may be added without
incrementing the format version. Version increments will be reserved for changes to existing 
chunk types. A conforming parser should ignore chunk types it does not recognize. 

## Top-level Chunk: `TEST`

Each `TEST` chunk represents a single CPU test case, containing multiple **subchunks**, concatenated.

---

## Subchunks inside a `TEST`

Each subchunk inside the `TEST` chunk is:

| Field       | Size (bytes) | Description                              |
|-------------|--------------|------------------------------------------|
| Chunk Type | 4          | ASCII string identifier (`NAME`, `BYTS`, `INIT`, `FINA`, `CYCL`, `HASH`, `IDX `) |
| Chunk Length | 4        | Length of payload |
| Index      | 4          | 0-based index of test in file |
| Chunk Data | Variable   | Payload bytes as described in the following sections |

---

## Subchunk Types and Payload Formats

### 1. `NAME`

- Length-prefixed UTF-8 string.
- Format:

| Field           | Size (bytes) | Description                 |
|-----------------|--------------|-----------------------------|
| Length     | 4            | uint32 length of name in bytes |
| Name String     | Variable     | ASCII encoded test name |

---

### 2. `BYTS`

- Raw instruction bytes that comprise the current instruction being tested.
- Format:

| Field           | Size (bytes) | Description                 |
|-----------------|--------------|-----------------------------|
| Length    | 4            | uint32 number of bytes |
| Bytes          | Variable     | Raw byte values |

---

### 3. `INIT` and `FINA`

- CPU state snapshots (initial and final).
- Composed of concatenated subchunks:

| Subchunk Type | Description         |
|---------------|---------------------|
| `REGS`        | Register data      |
| `RAM `        | RAM entries         |
| `QUEU`        | Queue data          |

---

#### a) `REGS`

- Contains registers present and their values. Only registers that were modified by the instruction are stored in the final state, so a bitmask is included that indicates whether a register should be parsed or ignored.
- Format:

| Field       | Size (bytes) | Description                              |
|-------------|--------------|------------------------------------------|
| Bitmask     | 2            | 16-bit bitmask indicating which registers are present (bit 0 = `ax`, bit 1 = `bx`, etc.) |
| Values      | 2 bytes each | Register values in order for each bit set in the bitmask, as 16-bit little-endian unsigned integers |

---

#### b) `RAM `

- List of memory address-value entries. These values should be written at their indicated registers before the start of the test.
- Format:

| Field       | Size (bytes) | Description                              |
|-------------|--------------|------------------------------------------|
| Entry Count | 4            | Number of RAM entries        |
| Entries     | 5 bytes each | Each entry contains 4-byte address + 1 byte value |

---

#### c) `QUEU`

- Contents of the processor instruction queue. The queue should be initialized before the test to the specified contents, if cycle-accurate testing is being performed.
- Format:

| Field       | Size (bytes) | Description                              |
|-------------|--------------|------------------------------------------|
| Length      | 4            | Number of bytes in queue     |
| Bytes      | Variable     | Raw queue bytes |

---

### 4. `CYCL`

- List of CPU bus cycle states.
- Format:

| Field       | Size (bytes) | Description                              |
|-------------|--------------|------------------------------------------|
| Cycle Count | 4            | Number of cycles (uint32 LE)              |
| Cycles      | 15 bytes each| Each cycle encoded as (in order):<br>• `pin_bitfield` (1 byte)<br>• `address_latch` (4 bytes, uint32)<br>• `segment_status` (1 byte enum)<br>• `memory_status` (1 byte bitfield)<br>• `io_status` (1 byte bitfield)<br>• `bhe_status` (1 byte)<br>• `data_bus` (2 bytes, uint16)<br>• `bus_status` (1 byte enum)<br>• `t_state` (1 byte enum)<br>• `queue_op_status` (1 byte enum)<br>• `queue_byte_read` (1 byte) |

See the main JSON documentation for explanation of these values.

---

### 5. `HASH`

- SHA-1 hash of the test from the source JSON. Can be used to uniquely identify a test in both JSON and MOO formats.
- Format:

| Field       | Size (bytes) | Description                              |
|-------------|--------------|------------------------------------------|
| Hash Data   | 20           | Raw 20-byte SHA-1 hash |

---

## Enumerations and Bitfields

### Segment Status (`segment_status`)

| Value | Meaning |
|-------|---------|
| 0     | ES      |
| 1     | SS    |
| 2     | CS or None    |
| 3     | DS    |
| 4     | Not valid    |

---

### Bus Status (`bus_status`)

An octal value representing the bus status as reported by the CPU's S0-S2 status lines.

| Value | Abbreviation | Meaning |
|-------|---------|---------|
| 0     | "INTA"  | Interrupt Acknowledge |
| 1     | "IOR"   | IO Read |
| 2     | "IOW"   | IO Write |
| 3     | "MEMR"  | Memory Read |
| 4     | "MEMW"  | Memory Write |
| 5     | "HALT"  | Halt |
| 6     | "CODE"  | Code Fetch |
| 7     | "PASV"  | Passive |

---

### T-State (`t_state`)

| Value | Meaning |
|-------|---------|
| 0     | "Ti"    |
| 1     | "T1"    |
| 2     | "T2"    |
| 3     | "T3"    |
| 4     | "T4"    |

---

### Queue Operation Status (`queue_op_status`)

| Value | Meaning |
|-------|---------|
| 0     | No Queue Operation    |
| 1     | First Byte Read From Queue  |
| 2     | Queue Emptied (Flushed)     |
| 3     | Subsequent Byte Read From Queue     |

---

### Memory and IO Status Bitfields (`memory_status` and `io_status`)

- Each is a 3-bit bitfield, representing the Write, Advanced Read, and Read signals, from Bit 0 to Bit 2.
---

