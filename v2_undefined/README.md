## 8088 V2_undefined

In the main test set, some undefined instruction forms that are less than useful and difficult to emulate were filtered out. 

This is a set of unfiltered CPU tests that includes those forms. Like the main test set, these were produced with an AMD D8088.

Up for the challenge? See if you can pass these tests.

### Per-Instruction Notes

 - **8F** - The forms of this instruction where reg != 0 are undefined. Behavior has been unpredictable across CPU models, but it seems to behave itself on the AMD D8088 with the Arduino DUE version of the validator.

 - **FE.2-FE.7**: The extensions 2-7 of the FE form are invalid, byte-sized versions of FE. As you can imagine, doing a far call through a byte operand is not a sensible thing to ask the CPU to do, asking it to do so through an 8-bit register even less so.

 - **FF.2-FF.7**: The extensions of 2-7 of the FE form are valid, except for their register forms. Although a call through a 16-bit register may have some chance of success, a far call through a 16-bit register faces the same issues as its 8-bit counterpart.

