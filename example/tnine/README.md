# Tnine Example Tests

This directory contains example tests for the tnine project.

## Overview

The example tests demonstrate how to use c-analyzer for simple C file.

## Running the Tests

To run the example tests, follow these steps:

1. Ensure you have [uv](https://docs.astral.sh/uv/) installed.
2. Run the tests using the following command:

    ```sh
    uv run c-analyzer.py example/tnine/tnine.c
    ```

## Note on Tests

Test "absence pametovych chyb" will fail on windows, because it uses valgrind to check for memory leaks.