"""
File: c-analyzer.py
Author: Josef Michalík
Date: 5/12/2024
Purpose: Analyze C code and provide statistics about it, similar to the C Analyzer tool VUT FIT uses.

Description:
This module contains functions/classes that analyze C code and provide statistics about it.

Functions:
- main(): Entry point, parses arguments and runs analysis/tests
- find_config_file(): Locates configuration file in directory
- _load_config(): Loads and parses JSON configuration
- _load_schema(): Loads JSON schema for config validation
- checkHeader(): Validates if file has proper header comment block
- analyze_functions(): Analyzes function metrics like length and complexity
- analyze_comments(): Checks comment coverage and uncommented blocks
- run_tests(): Executes configured test cases

Classes:
- ConfigParser: Handles loading and validating configuration files
- BaseAnalyzer: Base class for code analysis with compilation support
- CodeAnalyzer: Analyzes code style and structure metrics
- TestRunner: Executes test cases and validates outputs

Usage:
uv run c-analyzer.py <source_file> [--config <config_file>] [--mode {analyze,test,both}]
or
python c-analyzer.py <source_file> [--config <config_file>] [--mode {analyze,test,both}]

Notes:
Any additional notes or information that might be useful for understanding the code.

"""

import re
import subprocess
import json
import os
from typing import List, Dict, Tuple, Optional, TypedDict, Union, Literal, Any
from typing_extensions import NotRequired
import jsonschema
from difflib import unified_diff
from datetime import datetime


class CompilerConfig(TypedDict):
    cmd: str


class RunnerConfig(TypedDict):
    cmd: str


class TestCase(TypedDict):
    name: str
    preCommand: NotRequired[str]
    command: List[str]
    expected_status: int
    expected_output: NotRequired[str | bool]
    expected_stderr: NotRequired[str | bool]


class TestsConfig(TypedDict, total=False):
    file: str
    tests: List[TestCase]


class PenaltyItem(TypedDict):
    msg: str
    threshold: float

class AnalysisPenalties(TypedDict):
    penalties: Dict[str, PenaltyItem]

class ConfigSchema(TypedDict):
    compiler: CompilerConfig
    runner: RunnerConfig
    tests: NotRequired[TestsConfig]
    analysis: NotRequired[AnalysisPenalties]


class CompilationResult(TypedDict):
    stdout: str
    stderr: str
    success: int


class AnalyzedSchema(TypedDict):
    compilation: CompilationResult
    code_analysis: str


class ConfigParser:
    """Class for parsing configuration files"""

    def __init__(self, config_file: str) -> None:
        self.config_file = config_file
        if not config_file:
            self.config_file = self.find_config_file()
        self.config_data: ConfigSchema = self._load_config()
        self.schema = self._load_schema()
        self._validate_config()

    def find_config_file(self) -> str:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        config_files = list(filter(
            lambda x: x.endswith('.config.json'),
            os.listdir(dir_path)
        ))
        if not config_files:
            raise FileNotFoundError("No config file found")
        return os.path.join(dir_path, config_files[0])

    def _load_config(self) -> ConfigSchema:
        with open(self.config_file, 'r') as file:
            config = json.load(file)
            
        # If test file is specified, load and append tests
        if 'tests' in config and 'file' in config['tests']:
            test_file = config['tests']['file']
            test_file_path = os.path.join(os.path.dirname(self.config_file), test_file)
            
            try:
                with open(test_file_path, 'r') as test_file:
                    if 'tests' not in config['tests']:
                            config['tests']['tests'] = []
                            
                    test_data = json.load(test_file)
                    if 'tests' in test_data:
                        config['tests']['tests'].extend(test_data['tests'])
            except Exception as e:
                print(f"Warning: Failed to load test file: {e}")
                
        return config

    def _load_schema(self) -> Dict[str, Any]:
        if '$schema' not in self.config_data:
            raise ValueError("Config file must contain '$schema' field")

        schema_url = self.config_data['$schema']
        schema_path = os.path.join(
            os.path.dirname(self.config_file), schema_url)

        with open(schema_path, 'r') as file:
            return json.load(file)

    def _validate_config(self) -> None:
        jsonschema.validate(instance=self.config_data, schema=self.schema)

    def get_config(self) -> ConfigSchema:
        return self.config_data


class PenaltyConfig(TypedDict):
    msg: str
    threshold: float

class CodeBlock(TypedDict):
    line_num: int
    lines:int
    size: int


class BaseAnalyzer:
    """Base class for code analysis and test running"""
    source_file: str
    config: ConfigSchema
    executable: str

    def __init__(self, source_file: str, config: ConfigSchema) -> None:
        self.source_file = source_file
        self.config = config
        self.executable = self.source_file.rsplit('.', 1)[0]

    def run_compilation(self) -> CompilationResult:
        """Compile the source code and capture compilation log."""
        result = CompilationResult(stdout='', stderr='', success=False)
        try:
            name = self.executable
            compile_command = self.config['compiler']['cmd'].format(name=name)
            process = subprocess.run(compile_command, shell=True,capture_output=True, text=True)

            result['stdout'] = process.stdout
            result['stderr'] = process.stderr
            result['success'] = (process.returncode == 0)

        except Exception as e:
            result['stderr'] = f"Compilation error: {str(e)}"
            result['success'] = False

        return result

    def cleanup(self) -> None:
        """Clean up generated files"""
        try:
            if os.path.exists(self.executable):
                os.remove(self.executable)
            exe_with_extension = f"{self.executable}.exe"
            if os.path.exists(exe_with_extension):
                os.remove(exe_with_extension)
        except Exception as e:
            print(f"Warning: Failed to clean up executable: {e}")


class CodeAnalyzer(BaseAnalyzer):
    """Class for analyzing code style and structure"""
    analyzed_data: AnalyzedSchema
    analysis_config: Dict[str, PenaltyItem]

    def __init__(self, source_file: str, config: ConfigSchema) -> None:
        super().__init__(source_file, config)
        self.analyzed_data = {
            'compilation': self.run_compilation(),
            'code_analysis': ''
        }
        self.analysis_config = config.get('analysis', {}).get('penalties', {})
        self.analyze_code_style()

    def checkHeader(self, code: List[str]) -> bool:
        """Check if file has a header comment block of at least 3 lines"""
        header = code[:15]  # Check first 15 lines
        
        if len(header) < 3:
            return False

        comment_lines = 0
        in_comment = False
        
        for line in header:
            line = line.strip()
            if line.startswith('/*'):
                in_comment = True
                comment_lines += 1
            elif line.startswith('*/'):
                in_comment = False
                comment_lines += 1
                break
            elif in_comment:
                comment_lines += 1
                
        return comment_lines >= 3

    def print_analysis_penalty(self, line_num: int, penalty: str, more: Optional[str] = None, format_args: Optional[tuple] = None) -> None:
        """Print analysis penalty message"""
        file_msg = f"{self.source_file}"
        if line_num > 0:
            file_msg += f":{line_num}"
        config = self.analysis_config.get(penalty, {'msg': f'Unknown penalty: {penalty}'})
        msg = config['msg']
        if format_args:
            msg = msg.format(*format_args)
        print(f"{file_msg}: {msg}{f' ({more})' if more else ''}")

    def get_function_length(self, code_lines: List[str]) -> int:
        """
        Calculate the length of a function in lines of code.

        :param code_lines: List of code lines starting from function definition
        :return: Number of lines in the function
        """
        brace_count = 0
        length = 0

        for line in code_lines:
            line = line.strip()
            if not line:
                continue

            # Count opening and closing braces
            brace_count += line.count('{') - line.count('}')
            length += 1

            # If braces are balanced, we've reached the end of the function
            if brace_count == 0 and length >= 1:
                break

        return length

    def calculate_function_complexity(self, func_lines: List[str]) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        for line in func_lines:
            # Count conditional statements and loops
            complexity += line.count('if ') + line.count('while ') + line.count('for ')
            # Count logical operators (each creates a new path)
            complexity += line.count('&&') + line.count('||')
            # Count ternary operators
            complexity += line.count('?')
            # Count case statements
            complexity += line.count('case ') + line.count('default:')
        return complexity

    def analyze_function_args(self, line: str) -> int:
        """Count number of arguments in function declaration"""
        # Extract content between parentheses
        match = re.search(r'\((.*?)\)', line)
        if not match:
            return 0
            
        args = match.group(1).strip()
        if not args or args == "void":
            return 0
            
        return len(args.split(','))

    def analyze_functions(self, code: List[str]) -> None:
        """Analyze functions for issues"""
        i = 0
        while i < len(code):
            line = code[i].strip()
            
            # Match function declaration/definition
            match = re.match(r'^\s*(?:static\s+)?(?:[\w\*]+\s+)*(?:\*\s*)?(\w+)\s*\([^)]*\)\s*{?\s*$', line)
            if match:
                func_name = match.group(1)
                
                # Get function body
                brace_count = line.count('{')
                func_lines = [line]
                j = i + 1
                
                # Keep reading until function end (balanced braces)
                while j < len(code) and brace_count > 0:
                    line = code[j].strip()
                    if line:
                        brace_count += line.count('{') - line.count('}')
                        func_lines.append(line)
                    j += 1
                
                # Analyze the function
                arg_count = self.analyze_function_args(func_lines[0])
                if arg_count == 0:
                    self.print_analysis_penalty(i + 1, 'no_args', None, (func_name,))

                if len(func_lines) > self.analysis_config['long_function']['threshold']:
                    self.print_analysis_penalty(
                        i + 1, 'long_function', f'{len(func_lines)} řádků', (func_name,))

                complexity = self.calculate_function_complexity(func_lines)
                if complexity > self.analysis_config['complex_function']['threshold']:
                    self.print_analysis_penalty(
                        i + 1, 'complex_function', f'{complexity} cest', (func_name,))
                
                # Skip to end of function
                i = j
                continue
            
            i += 1

    def analyze_comments(self, code: List[str], commented_lines: int, large_blocks: List[CodeBlock | None],code_len: int) -> None:
        """Analyze code comments and add relevant issues"""
        comment_ratio = (commented_lines / code_len)
        if comment_ratio < self.analysis_config['low_comments']['threshold']:
            self.print_analysis_penalty(
                0, 'low_comments', f'{int(comment_ratio*100)}%')
            
        for block in large_blocks:
            if block and block['lines'] > self.analysis_config['uncommented_blocks']['threshold']:
                self.print_analysis_penalty(
                    block['line_num'], 'uncommented_blocks', f'{block["lines"]} řádků')

    def analyze_explicit_casts(self, line: str, line_num: int) -> None:
        """Analyze code for explicit type casts"""
        # Not reliable
        # cast_matches = re.finditer(r'\(([\w\s]+\s*\*?)\)\s*\w+', line)
        # for match in cast_matches:
        #     self.print_analysis_penalty(
        #         line_num, 'type_cast', match.group(1))    

    def analyze_line_length(self, line: str, line_num: int) -> None:
        """Analyze line length and add relevant issues"""
        if len(line) > self.analysis_config['long_line']['threshold']:
            self.print_analysis_penalty(
                line_num, 'long_line', f'{len(line)} znaků')
    
    def analyze_code_style(self) -> None:
        """Analyze code style"""
        print("============ Analyza kodu ===============")
        with open(self.source_file, 'r') as f:
            code = f.readlines()

        if (not self.checkHeader(code)): print("hlavička nenalezena")

        commented_lines = 0
        large_blocks: List[CodeBlock | None] = []
        # Only count non-empty lines

        # Track uncommented blocks and lines
        current_block: CodeBlock | None = {'line_num': 1, 'lines': 0, 'size': 0}
        in_block_comment = False
        code_len = 0

        for i, line in enumerate(code, 1):
            self.analyze_line_length(line, line_num=i)
            line = line.strip()
            
            if not line:
                continue
            
            code_len += 1

            self.analyze_explicit_casts(line, i)
            
            # Count comments
            if line.lstrip().startswith('/*'):
                if line.rstrip().endswith('*/'):
                    commented_lines += 1
                else:
                    in_block_comment = True
                    commented_lines += 1
                    if current_block:
                        large_blocks.append(current_block)
                        current_block = None
                continue
                
            if line.rstrip().endswith('*/'):
                in_block_comment = False
                commented_lines += 1
                continue
                
            if in_block_comment or line.startswith('//') or '//' in line:
                commented_lines += 1
                if current_block:
                    large_blocks.append(current_block)
                    current_block = None
                continue
                
            # Track non-comment blocks
            if not current_block:
                current_block = {'line_num': i, 'lines': 1, 'size': len(line)}
            else:
                current_block['lines'] += 1
                current_block['size'] += len(line)

        if current_block:
            large_blocks.append(current_block)

        self.analyze_comments(code, commented_lines, large_blocks, code_len)
        
        self.analyze_functions(code)


class TestRunner(BaseAnalyzer):
    """Class for running tests"""

    def __init__(self, source_file: str, config: ConfigSchema) -> None:
        super().__init__(source_file, config)
        self.run_tests()

    def run_tests(self) -> None:
        """Run all configured tests"""
        compilation_result = self.run_compilation()
        if not compilation_result['success']:
            print("0:spatne: compilation")
            print("# Compilation failed")
            return

        if 'tests' not in self.config or 'tests' not in self.config['tests']:
            return
        
        print()
        print("====== Testy funkcionality ======")
        
        exe_dir = os.path.dirname(os.path.abspath(self.executable))
        exe_name = os.path.join(".", os.path.basename(self.executable))
        cmd = [os.path.join(exe_dir, exe_name)]
        
        for test in self.config['tests']['tests']:
            self._run_single_test(test, cmd, exe_dir)

    def _run_single_test(self, test: TestCase, cmd: list[str], exe_dir: str) -> None:
        """Run a single test case and print result"""
        cmd = cmd.copy()
        for arg in test['command']:
            if '/' in arg:
                file_name = os.path.basename(arg)
                file_dir = os.path.dirname(arg)
                arg = os.path.join(file_dir, file_name)
            cmd.append(arg)
        cmd_str = test.get("preCommand", "") + " " + ' '.join(cmd)
        
        try:
            result = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True,
                text=True,
                cwd=exe_dir
            )

            actual_output = result.stdout.strip()
            actual_stderr = result.stderr.strip()
            expected_output = test.get('expected_output')
            expected_stderr = test.get('expected_stderr')
            
            if isinstance(expected_output, bool):
                output_matches = bool(actual_output) if expected_output else not actual_output
            else:
                output_matches = (not expected_output or actual_output == expected_output.strip())

            if isinstance(expected_stderr, bool):
                stderr_matches = bool(actual_stderr) if expected_stderr else not actual_stderr
            else:
                stderr_matches = (not expected_stderr or actual_stderr == expected_stderr.strip())
            
            test_passed = (
                result.returncode == test['expected_status'] and
                output_matches and
                stderr_matches
            )
            
            if test_passed:
                print(f"ok: {test['name']}")
            else:
                print(f"0:spatne: {test['name']}")
                if actual_output != expected_output:
                    print("# Neodpovida vzorovemu vystupu")
                    # Generate diff using unified_diff
                    expected_lines = str(expected_output).splitlines(keepends=True)
                    actual_lines = str(actual_output).splitlines(keepends=True)
                    test_name = test['name']
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    
                    diff = unified_diff(
                        expected_lines, 
                        actual_lines,
                        fromfile=f"testdata/{test_name}",
                        tofile=test_name,
                        fromfiledate=now,
                        tofiledate=now
                    )
                    
                    for line in diff:
                        print(f"# {line}", end='')

        except Exception as e:
            print(f"0:spatne: {test['name']}")
            print(f"# {str(e)}")


def main() -> None:
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Code Review Generator')
    parser.add_argument('source_file', help='Source code file to analyze')
    parser.add_argument('--config', default='',
                       help='Configuration file path (optional)')
    parser.add_argument('--mode', choices=['analyze', 'test', 'both'],
                       default='both', help='Operation mode')

    args = parser.parse_args()
    config = ConfigParser(args.config)
    config_data = config.get_config()

    # if args.mode in ['analyze', 'both']:
    #     analyzer = CodeAnalyzer(args.source_file, config_data)

    # if args.mode in ['test', 'both']:
    #     runner = TestRunner(args.source_file, config_data)
        
    match args.mode:
        case 'analyze':
            analyzer = CodeAnalyzer(args.source_file, config_data)
            analyzer.cleanup()
        case 'test':
            runner = TestRunner(args.source_file, config_data)
            runner.cleanup()
        case 'both':
            analyzer = CodeAnalyzer(args.source_file, config_data)
            runner = TestRunner(args.source_file, config_data)
            runner.cleanup()
        


if __name__ == "__main__":
    main()
