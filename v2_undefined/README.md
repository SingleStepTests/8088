## 8088 V2_undefined

In the main test set, some undefined instruction forms that are less than useful and difficult to emulate were filtered out. 

This is a set of unfiltered CPU tests that includes those forms. Like the main test set, these were produced with an AMD D8088.

Up for the challenge? See if you can pass these tests.

### Update 2025-03-16:

 - As it turns out, the group opcodes 3 and 5, CALL FAR and JUMP FAR, cannot be traditionally emulated when register operands are specified.
   Due to assumptions made by the microcode, these routines use the state of internal registers (IND, tmpb and tmpa) that are uninitialized when the address calculation to fetch a memory operand 
   is not peformed. 

   This means that these instructions leak the internal state of registers via the address used to fetch the new segment, and the values used to set the new code segment and program counter.
   The test suite does not give you enough information to determine what these values should be. The values observed in the test suite are no doubt influenced by the CPU register set up and queue 
   filling routines, and therefore cannot give you useful information about the true behavior of these undefined forms.

### Per-Instruction Notes

 - **8F** - The forms of this instruction where reg != 0 are undefined. Behavior has been unpredictable across CPU models, but it seems to behave itself on the AMD D8088 with the Arduino DUE version of the validator.

 - **FE.2-FE.7**: The extensions 2-7 of the FE form are invalid, byte-sized versions of FE. As you can imagine, doing a far call through a byte operand is not a sensible thing to ask the CPU to do, asking it to do so through an 8-bit register even less so.

 - **FF.2-FF.7**: The extensions of 2-7 of the FF form are valid, except for their register forms. Although a call through a 16-bit register may have some chance of success, a far call through a 16-bit register faces the same issues as its 8-bit counterpart.

