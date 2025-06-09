# JSON Utility scripts

These are some miscellaneous Python utilities for working with JSON test suites.

- addhash.py 
    - This utility will add a SHA1 hash to each test in a test collection. This provides a unique identifier for a test, which is often useful.
- extract.py
    - This utility will find and extract a specific test either by a hash created by the addhash utility, or its numeric index.
- remove.py
    - This utility will find and remove a specific test either by a hash created by the addhash utility, or its numeric index.
- subset.py
    - This utility will create a subset of larger test.
- checkdups.py
    - This utility will check a test suite for duplicate tests.
- diff_flags.py
    - This utility will report flag changes observed in a test file.
- diff_flags_dir.py
    - This utility will report flag changes observed in all test files within a directory.
- condense.py 
    - This utility will pretty-print a JSON test file in a condensed format.
- convert_binary.py
    - This utility will convert tests in JSON format to binary MOO format.
- viewer.py
    - A simple example of showing a JSON test in a more easily readable format, with a table of cycle states, and values in hexadecimal.
- moo_parser.c
    - C example code for parasing the MOO binary test format.
