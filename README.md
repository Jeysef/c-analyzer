# C-analyzer

This project is a simple C file analyzer. It can analyze C files and run test cases on them.

It tries to adhere to the code analysis tests used in the [FIT VUTBR](https://www.fit.vut.cz/) course [IZP](https://www.fit.vut.cz/study/course/IZP/).

**warning**: This project is not affiliated with the course or the university. It is a personal project created to help students analyze their code and run test cases. It cannot be used as a proof of correctness for the course.

## Usage
Run the code analyzer on a C source file:

```sh
uv run c-analyzer.py <source_file> [--config <config_file>] [--mode <mode>]
```

parameters:
- `<source_file>`: path to the C source file to analyze
- `--config <config_file>`: (Optional) Path to the configuration file. If not provided, the script will look for a `.config.json` file in the current directory.
- `--mode <mode>`: (Optional) Operation mode. Options are:
  - `analyze`: Runs only the code analysis.
  - `test`: Runs only the tests.
  - `both`: Runs both code analysis and tests (default).

## Example

```sh
python c-analyzer.py main.c --mode both
```

## Configuration

The analyzer uses a configuration file in JSON format to specify compiler commands, test cases, and analysis penalties. If no configuration file is provided, it will look for a `.config.json` file in the current directory.

## Dependencies
This project requires the following Python packages:

- `jsonschema`
- `typing_extensions`
Install them using "uv":
    
    ```sh
    uv install jsonschema typing_extensions
    ```

## Notes
Refer to the comments and documentation within the c-analyzer.py script for more details.

## Motivation

This project was created after being given poor scores on the IZP course at FIT VUTBR, mainly due to the lack of test cases and code analysis. 

The goal is to provide a tool that can help students analyze their code and run test cases to ensure it meets the requirements of the course.

## Future Work

I don't plan to keep the project up to date, but I will accept pull requests if anyone wants to contribute.
The analysis is not perfect, nor complete, mainly because it checks the text of the code and **NOT** the abstract syntax tree with package like `pycparser`. 