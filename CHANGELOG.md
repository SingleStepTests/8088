## v1.2.1 5/25/2024
 - Fixed some final IP addresses formatted as negative decimals

## v1.2.0 5/9/2024
 - Renamed 8088.json to metadata.json, moved opcodes to 'opcodes' key of parent object, and added additional metadata fields to parent object.
 - Renamed 'test_hash' key to 'hash' and 'test_num' key to 'idx'
 - Changed hash algorithm from SHA256 to SHA1 to save space
 - Removed register entries from 'final' state that didn't change
 - Removed ram entries from 'final' state that didn't change
 - Corrected final IP for F6.7 and F7.7 when an exception occured
 
## v1.1.1 1/7/2023
 - Fixed incorrect final register state in some tests within F6.7

## v1.1.0 10/21/2023
 - Improved disassembler; validated disassembly against iced-x86
 - Added test hashes

## v1.0.1 9/12/2023
 - Update 8D to remove reg, reg forms

## v1.0.0 Initial Release
 - Initial release of 8088 CPU Test Suite
