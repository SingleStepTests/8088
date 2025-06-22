## 8088 V2

This is a set of 8088 CPU tests produced by Daniel Balsom using the [Arduino8088](https://github.com/dbalsom/arduino_8088) interface and the [MartyPC](https://github.com/dbalsom/martypc) emulator.

### Current version: 2.0.1

 - The ```v1``` directory contains the older 1.X version of this test suite. It is retained for reference only. I encourage everyone to use V2 of the test suite.
 - The ```v2``` directory contains the current version of the 8088 test suite.
 - The ```v2_binary`` directory contains the the test suite in a binary format, MOO, gzipped.
 - The ```v2_undefined``` directory contains a set of test for certain undefined instruction forms that are tricky and less useful to emulate.

### Changes from 8088 Test Suite V1

V2 introduces a few changes to the test format and conventions.

 - The address column in the 'cycles' array is now represents the state of the address/data bus per-cycle. It is up to you to latch the address on ALE if you wish.
   Having the cycle-accurate output of the bus lines enables more accurate emulation verification.
 - The values for 'ram' are no longer sorted by address; but should appear in the order in which they were accessed.
 - The final state only includes memory and register values that have changed. The entire flags register is included if any flag has changed.
 - Half of the instructions execute from a full instruction prefetch queue. See "Using The Tests" for more information on how to handle this.
 - The model of CPU used to generate the tests was changed to an NMOS 8088, enabled by improvements to the Arduino8088's performance.
 - More instructions have been exempted from receiving segment override prefixes when it is clear they cannot possibly have an effect.
 - Undefined flag state is now correctly captured from the physical CPU.

### About the Tests

These tests are produced with an AMD D8088 (8441DMA) CPU dated 1982, running in Maximum Mode. Bus signals are provided via i8288 emulation.

10,000 tests are provided per opcode, with the following exceptions:

- String instructions are limited to 2,000 tests due to their large size, even when masking CX to 7 bits.
- Shift and rotate instructions that use CL (D2, D3) are limited to 5,000 tests again due to size constraints, even when masking CL to 6 bits.
- INC and DEC instructions with fixed register operands (40-4F) are limited to 1,000 tests as they are trivial.
- Flag instructions (F5,F8-FD) are limited to 1,000 tests as they are trivial.

All tests assume a full 1MB of RAM is mapped to the processor and writable. Bear in mind that on the 8088, the address space wraps around at FFFFF.

No wait states are incurred during any of the tests. The interrupt and trap flags are not exercised. 

This test set exercises the 8088's processor instruction queue. Half of provided instructions will execute from a full instruction queue.

### Using the Tests

The simplest way to run each test is to override your emulated CPU's normal reset vector (FFFF:0000) to the CS:IP of the test's initial state, then reset the CPU. 

#### Non-Prefetched Tests

- If the initial queue state is empty, the instruction is not prefetched. Once the reset procedure completes, the instruction should begin normally by being fetched after the reset routine has completed.

#### Prefetched Tests

- If the test specifies an initial queue state, the provided initial queue contents should be set after the CPU reset routine flushes the instruction queue. This should trigger your emulator to suspend prefetching since the queue is full. In my emulator, I provide the CPU with a vector of bytes to install in the queue before I call ```cpu.reset()```. You could also pass your reset method a vector of bytes to install.

- You will need to add the length of the queue contents to your PC register (or adjust the reset vector IP) so that fetching begins at the correct address. 

- Once you read the first instruction byte out of the queue to begin test execution, prefetching should be resumed since there is now room in the queue. It takes two cycles to begin a fetch after reading from a full queue, therefore tests that specify an initial queue state will start with two 'Ti' cycle states.

- If you're not interested in per-cycle validation, you can ignore the queue fields entirely.

### Why Are Instructions Longer Than Expected?

Instruction cycles begin from the cycle in which the CPU's queue status lines indicate that an instruction "First Byte" has been fetched - this may be an optional instruction prefix, in which case there will be multiple First Byte statuses until the first byte that is a non-prefixed opcode byte is read. If the test is starting from an empty prefetch queue, the final opcode byte and any modrm or displacement must be read from the bus before instruction execution can begin.

Instructions cycles end when the queue status lines indicate that the first byte of the next instruction has been read from the queue. If the instruction started fully prefetched and the next instruction byte was present in the queue at the end of the instruction, the instruction cycles should reflect the documented "best case" instruction timings. If the queue was empty at the end of execution, the extra cycles spent fetching the next instruction byte may lengthen the instruction from documented timings. There is no indication from the CPU when an instruction ends - only when a new one begins.

### Segment Override Prefixes

Random segment override prefixes have been prepended to a percentage of instructions, even if they may not do anything. This isn't completely useless - a few bugs have been found where segment overrides had an effect when they should not have.

### String Prefixes

String instructions may be randomly prepended by a REP, REPE, REPNE instruction prefix. In this event, CX is masked to 7 bits to produce reasonably sized tests (A string instruction with CX==65535 would be over a million cycles in execution). 

### Instruction Prefetching

All bytes fetched after the initial instruction bytes are set to 0x90 (144) (NOP). Therefore, the queue contents at the end of all tests will contain only NOPs, with a maximum of 3 (since one has been read out).

### Test Format

The 8086 test suite comes in two formats, JSON and a simple chunked binary format I call `MOO` (Machine Opcode Operation).
If your language of choice lacks great options for parsing JSON (such as C) you may prefer the binary format tests.

You can find more information about the binary format in README.md in the /v2_binary directory. There is also an example MOO parser in C under the /tools directory.

Information on the JSON format proceeds below.

Sample test:
```json
{
    "name": "add byte [ss:bp+di-64h], cl",
    "bytes": [0, 75, 156],
    "initial": {
        "regs": {
            "ax": 21153,
            "bx": 59172,
            "cx": 33224,
            "dx": 61687,
            "cs": 12781,
            "ss": 7427,
            "ds": 600,
            "es": 52419,
            "sp": 49014,
            "bp": 9736,
            "si": 52001,
            "di": 10025,
            "ip": 694,
            "flags": 62546
        },
        "ram": [
            [205190, 0],
            [205191, 75],
            [205192, 156],
            [205193, 144],
            [138493, 20]
        ],
        "queue": [0, 75, 156, 144]
    },
    "final": {
        "regs": {
            "ip": 697,
            "flags": 62594
        },
        "ram": [
            [138493, 220]
        ],
        "queue": [144, 144, 144]
    },
    "cycles": [
        [0, 62369, "--", "---", "---", 0, 0, "PASV", "Ti", "F", 0],
        [0, 62369, "--", "---", "---", 0, 0, "PASV", "Ti", "S", 75],
        [1, 205194, "--", "---", "---", 0, 0, "CODE", "T1", "-", 0],
        [0, 139658, "CS", "R--", "---", 0, 0, "CODE", "T2", "-", 0],
        [0, 139664, "CS", "R--", "---", 0, 144, "PASV", "T3", "-", 0],
        [0, 139664, "CS", "---", "---", 0, 0, "PASV", "T4", "-", 0],
        [1, 205195, "--", "---", "---", 0, 0, "CODE", "T1", "-", 0],
        [0, 139659, "CS", "R--", "---", 0, 0, "CODE", "T2", "S", 156],
        [0, 139664, "CS", "R--", "---", 0, 144, "PASV", "T3", "-", 0],
        [0, 139664, "CS", "---", "---", 0, 0, "PASV", "T4", "-", 0],
        [1, 205196, "--", "---", "---", 0, 0, "CODE", "T1", "-", 0],
        [0, 139660, "CS", "R--", "---", 0, 0, "CODE", "T2", "-", 0],
        [0, 139664, "CS", "R--", "---", 0, 144, "PASV", "T3", "-", 0],
        [0, 139664, "CS", "---", "---", 0, 0, "PASV", "T4", "-", 0],
        [1, 138493, "--", "---", "---", 0, 0, "MEMR", "T1", "-", 0],
        [0, 72957, "SS", "R--", "---", 0, 0, "MEMR", "T2", "-", 0],
        [0, 72724, "SS", "R--", "---", 0, 20, "PASV", "T3", "-", 0],
        [0, 72724, "SS", "---", "---", 0, 0, "PASV", "T4", "-", 0],
        [0, 72724, "--", "---", "---", 0, 0, "PASV", "Ti", "-", 0],
        [0, 72724, "--", "---", "---", 0, 0, "PASV", "Ti", "-", 0],
        [0, 72724, "--", "---", "---", 0, 0, "PASV", "Ti", "-", 0],
        [0, 72724, "--", "---", "---", 0, 0, "PASV", "Ti", "-", 0],
        [0, 72724, "--", "---", "---", 0, 0, "PASV", "Ti", "-", 0],
        [0, 72724, "--", "---", "---", 0, 0, "PASV", "Ti", "-", 0],
        [0, 72724, "--", "---", "---", 0, 0, "PASV", "Ti", "-", 0],
        [1, 138493, "--", "---", "---", 0, 0, "MEMW", "T1", "-", 0],
        [0, 72924, "SS", "-A-", "---", 0, 0, "MEMW", "T2", "-", 0],
        [0, 72924, "SS", "-AW", "---", 0, 220, "PASV", "T3", "-", 0]
    ],
    "hash": "1cef51a56be51f883826f6611a489dfbc35dfdf3",
    "idx": 0
},
```
- `name`: A user-readable disassembly of the instruction.
- `bytes`: The raw bytes that make up the instruction.
- `initial`: The register, memory and instruction queue state before instruction execution.
- `final`: Changes to registers and memory, and the state of the instruction queue after instruction execution.
    - Registers and memory locations that are unchanged from the initial state are not included in the final state.
    - The entire value of `flags` is provided if any flag has changed.
- `hash`: A SHA1 hash of the test JSON. It should uniquely identify any test in the suite.
- `idx`: The numerical index of the test within the test file.

### Cycle Format

If you are not interested in writing a cycle-accurate emulator, you can ignore this section.

The `cycles` list contains sub lists, each corresponding to a single CPU cycle. Each contains several fields. From left to right, the cycle fields are:  

 - Pin bitfield
 - Multiplexed bus
 - Segment status
 - Memory status
 - IO status
 - BHE (Byte high enable) status
 - Data bus
 - Bus status
 - T-state
 - Queue operation status
 - Queue byte read

The first column is a bitfield representing certain chip pin states. 

 - Bit #0 of this field represents the ALE (Address Latch Enable) pin output, which in Maximum Mode is output by the i8288. This signal is asserted on T1 to instruct the PC's address latches to store the current address. This is necessary since the address and data lines of the 8088 are multiplexed, and a full, valid address is only on the bus while ALE is asserted. Thus the second column represents the value of the address latch, and not the address bus itself (which may not be valid in a given cycle).
 - Bit #1 of this field represents the INTR pin input. This is not currently exercised, but may be in future test releases.
 - Bit #2 of this field represents the NMI pin input. This is not currently exercised, but may be in future test releases.

Tne Multiplexed bus value is the 20-bit value representing the entire bus read directly from the CPU each cycle. It contains a valid address only when ALE is asserted on T1.

The segment status indicates which segment is in use to calculate addresses by the CPU, using segment-offset addressing. This field represents the S3 and S4 status lines of the 8088.

The memory status field represents outputs of the attached i8288 Bus Controller. From left to right, this field will contain RAW or ---.  R represents the MRDC status line, A represents the AMWC status line, and W represents the MWTC status line. These status lines are active-low. A memory read will occur on T3 or the last Tw t-state when MRDC is active. A memory write will occur on T3 or the last Tw t-state when AMWC is active. At this point, the value of the data bus field will be valid and will represent the byte read or written.

The IO status field represents outputs of the attached i8288 Bus Controller. From left to right, this field will contain RAW or ---.  R represents the IORC status line. A represents the AIOWC status line. W represents the IOWC status line. These status lines are active-low. An IO read will occur on T3 or the last Tw t-state when IORC is active. An IO write will occur on T3 or the last Tw t-state when AIOWC is active. At this point, the value of the data bus field will be valid and will represent the byte read or written.

The BHE status pin on the 8086 indicates whether the upper byte of the data bus is driven. This pin does not exist on the 8088, but is provided in the test format for compatibility with the [8086 Test Suite](https://github.com/SingleStepTests/8086).

The data bus indicates the value of the last 8 bits of the multiplexed bus. It is typically only valid on T3. 

The bus status lines indicate the type of bus m-cycle currently in operation. Either INTA, IOR, IOW, MEMR, MEMW, HALT, CODE, or PASV.  These states represent the S0-S2 status lines of the 8088.

The T-state is the current T-state of the CPU. Since this state is not exposed by the CPU, it is calculated based on bus activity.

The queue operation status will contain either F, S, E or -. F indicates a "First Byte" of an instruction or instruction prefix has been read.  S indicates a "Subsequent" byte of an instruction has been read - either a modr/m, displacement, or operand. E indicates that the instruction queue has been Emptied/Flushed. All queue operation statuses reflect an operation that actually occurred on the previous cycle.  This field represents the QS0 and QS1 status lines of the 8088. 

When the queue operation status is not '-', then the value of the queue byte read field is valid and represents the byte read from the queue. 

For more information on the 8088 and 8288 status lines, see their respective white papers.

### Undefined Instructions

Note that these tests include many undocumented/undefined opcodes and instruction forms. The 8088 has no concept of an invalid instruction, and will perform some task for any provided sequence of instruction bytes. Additionally, flags may be changed by documented instructions in ways that are officially undefined.

### Per-Instruction Notes

 - **0F**: POP CS is temporarily omitted from V2 of the test set.
 - **8F**: The behavior of 8F with reg != 0 is undefined. If you can figure out the rules governing its behavior, please let us know.
 - **9B**: WAIT is not included in this test set.
 - **8C,8E**: These instructions are only defined for a reg value of 0-3, however only the first two bits are checked, so the test set contains random values for reg.
 - **8D,C4,C5**: 'r, r' forms of LEA, LES, LDS are undefined. These forms are not included in this test set due to disruption of the last calculated EA by the CPU set up routine.
 - **A4-A7,AA-AF**: CX is masked to 7 bits. This provides a reasonable test length, as the full 65535 value in CX with a REP prefix could result in over one million cycles.
 - **C6,C7**: Although the reg != 0 forms of these instructions are officially undefined, this field is ignored. Therefore, the test set contains random values for reg.
 - **D2,D3**: CL is masked to 6 bits. This shortens the possible test length, while still hopefully catching the case where CL is improperly masked to 5 bits (186+ behavior).
 - **E4,E5,EC,ED**: All forms of the IN instruction should return 0xFF on IO read.
 - **F0, F1**: The LOCK prefix is not exercised in this test set.
 - **F4**: HALT is not included in this test set.
 - **D4, F6.6, F6.7, F7.6, F7.7** - These instructions can generate a divide exception (more accurately, a Type-0 Interrupt). When this occurs, cycle traces continue until the first byte of the exception handler is fetched and read from the queue. The IVT entry for INT0 is set up to point to 1024 (0400h).
     - NOTE: On the 8088 specifically, the return address pushed to the stack on divide exception is the address of the next instruction. This differs from the behavior of later CPUs and generic Intel IA-32 emulators.
 - **F6.7, F7.7** - Presence of a REP prefix preceding IDIV will invert the sign of the quotient, therefore REP prefixes are prepended to 10% of IDIV tests. This was only recently discovered by reenigne.
 - **FE**: The forms with reg field 2-7 are undefined and are not included.

### metadata.json

If you are not interested in emulating the undefined behavior of the 8088, you can use the included metadata.json file which lists which instructions are undocumented or undefined and provides masks for undefined flags.

```json
{
    "url": "https://github.com/SingleStepTests/8088/",
    "version": "2.0.0",
    "syntax_version": 2,
    "cpu": "8088",
    "cpu_detail": "AMD D8088 8441DMA (C)1982",
    "generator": "arduino8088",
    "date": "2024",
    "opcodes": {
        "00": {
            "status": "normal"
        },
        "01": {
            "status": "normal"
        },
        "02": {
            "status": "normal"
        },
        "03": {
            "status": "normal"
        },
        ...
```

In metadata.json, opcodes are listed as object keys under the 'opcodes' field, each key being the opcode hexadecimal string representation padded to two digits. Each opcode entry has a 'status' field which may be 'normal', 'prefix', 'alias', 'undocumented', 'undefined', or 'fpu'.

An opcode marked 'prefix' is an instruction prefix. These opcodes will not have individual tests.
An opcode marked 'alias' is simply an alias for another instruction. These exist because the mask that determines which microcode address maps to which opcode is not always perfectly specific. 
An opcode marked 'undocumented' has well-defined and potentially useful behavior, such as SETMO and SETMOC. 
An opcode marked 'undefined' likely has unusual or unpredictable behavior of limited usefulness.
An opcode marked 'fpu' is an FPU instruction (ESC opcode).

If present, the 'flags' field indicates which flags are undefined after the instruction has executed. A flag is either a letter from the pattern `odiszapc` indicating it is undefined, or a period, indicating it is defined. The 'flags-mask' field is a 16 bit value that can be applied with an AND to the flags register after instruction execution to clear any flags left undefined.

An opcode may have a 'reg' field which will be an object of opcode extensions/register specifiers represented by single digit string keys - this is the 'reg' field of the modrm byte.  Certain opcodes may be defined or undefined depending on their register specifier or opcode extension. Therefore, each entry within this 'reg' object will have the same fields as a top-level opcode object. 

### Special Thanks

Thanks to Folkert van Heusden for his assistance in generating the V1 test suite.

