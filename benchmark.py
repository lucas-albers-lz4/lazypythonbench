#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json
import os
from tabulate import tabulate
import re

def ensure_requirements(python_path):
    """Ensure all required packages are installed for current user"""
    env = os.environ.copy()
    env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    
    requirements = ["pyperf", "pyperformance"]
    print(f"Checking requirements for {python_path}...")
    
    for package in requirements:
        try:
            subprocess.run(
                [python_path, "-m", "pip", "show", package], 
                capture_output=True, 
                check=True,
                env=env
            )
            print(f"✓ {package} is already installed")
        except subprocess.CalledProcessError:
            print(f"Installing {package}...")
            subprocess.run(
                [python_path, "-m", "pip", "install", "--user", package],
                check=True,
                env=env
            )

def create_virtualenv(python_path, venv_path):
    """Create a virtual environment quietly unless there's an error"""
    try:
        subprocess.run(
            [python_path, "-m", "venv", venv_path],
            stdout=subprocess.DEVNULL,  # Suppress standard output
            stderr=subprocess.PIPE,     # Capture error output
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtualenv: {e.stderr.decode()}")

def run_benchmark(python_path, output_dir):
    """Run minimal benchmarks for testing report generation"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    python_version = subprocess.check_output([python_path, "-V"]).decode().split()[1]
    output_file = output_dir / f"python{python_version}_{timestamp}.json"
    
    # Set environment variables to suppress pip and virtualenv output
    env = os.environ.copy()
    env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    env['PYTHONWARNINGS'] = 'ignore:DEPRECATION'
    env['VIRTUALENV_NO_PERIODIC_UPDATE'] = '1'
    env['PIP_QUIET'] = '1'
    env['VIRTUALENV_QUIET'] = '1'
    env['PIP_NO_INPUT'] = '1'
    env['PIP_PROGRESS_BAR'] = 'off'
    env['PIP_NO_COLOR'] = '1'
    env['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'
    
    # Minimal set of fast benchmarks with reduced iterations
    cmd = [
        python_path, "-m", "pyperformance", "run",
        "--python", python_path,
        "--benchmarks", "json_dumps,richards",
        "--fast",
        "--output", str(output_file),
        "--inherit-environ", "PIP_DISABLE_PIP_VERSION_CHECK,PYTHONWARNINGS,VIRTUALENV_NO_PERIODIC_UPDATE,PIP_QUIET,VIRTUALENV_QUIET,PIP_NO_INPUT,PIP_PROGRESS_BAR,PIP_NO_COLOR"
    ]
    
    try:
        print(f"\nRunning minimal benchmarks with {python_path}...")
        subprocess.run(cmd, env=env, check=True)
        print(f"Benchmark results saved to: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error running benchmarks: {e}")
        return None

def generate_test_comparison_report(files, output_dir):
    """Generate a focused comparison report of test failures"""
    report_file = output_dir / f"test_comparison_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"
    
    results = []
    for file in files:
        with open(file) as test_file:
            data = json.load(test_file)
            results.append(data)
    
    # Prepare table data
    headers = ["Python Version", "Tests Run", "Passed", "Failed"]
    table_data = [
        [
            r['python_version'], 
            r['tests_run'], 
            r['tests_run'] - r['tests_failed'],
            r['tests_failed']
        ]
        for r in results
    ]
    
    with open(report_file, 'w') as f:
        # Main summary with tabulate
        f.write("# Python Test Suite Comparison Report\n\n")
        f.write(tabulate(table_data, headers=headers, tablefmt="pipe", numalign="right"))
        f.write("\n\n")
        
        # Failed Tests by Version
        f.write("## Failed Tests by Version\n\n")
        has_failures = False
        for result in results:
            if result['failed_tests']:
                has_failures = True
                f.write(f"### Python {result['python_version']}\n")
                for test in result['failed_tests']:
                    f.write(f"- {test['name']}: {test['error']}\n")
                f.write("\n")
        if not has_failures:
            f.write("*No test failures in any version*\n\n")
        
        # Tests Failing in All Versions
        f.write("## Tests Failing in All Versions\n\n")
        all_failures = [set((test['name'], test['error']) for test in result['failed_tests']) for result in results]
        common_failures = set.intersection(*all_failures)
        
        if common_failures:
            for name, error in sorted(common_failures):
                f.write(f"- {name}\n  {error}\n")
            f.write("\n")
        else:
            f.write("*No tests fail in all versions*\n\n")
        
        # Failure Differences
        f.write("## Failure Differences Between Versions\n\n")
        for i in range(len(results)-1):
            base = results[i]
            compare = results[i+1]
            f.write(f"### {base['python_version']} → {compare['python_version']}\n\n")
            
            # Create sets of test failures with their full error messages
            base_failures = {(test['name'], test['error']) for test in base['failed_tests']}
            compare_failures = {(test['name'], test['error']) for test in compare['failed_tests']}
            
            # Find new and fixed failures
            new_failures = compare_failures - base_failures
            fixed_failures = base_failures - compare_failures
            
            if new_failures:
                f.write(f"New failures in {compare['python_version']}:\n")
                for name, error in sorted(new_failures):
                    f.write(f"- {name}\n  {error}\n")
                f.write("\n")
            
            if fixed_failures:
                f.write(f"Fixed in {compare['python_version']} (failed in {base['python_version']}):\n")
                for name, error in sorted(fixed_failures):
                    f.write(f"- {name}\n  {error}\n")
                f.write("\n")
            
            if not new_failures and not fixed_failures:
                f.write("*No differences in test failures*\n\n")
    
    return report_file

def compare_results(file1, file2):
    """Compare two benchmark result files using pyperf"""
    cmd = ["python3.9", "-m", "pyperf", "compare", str(file1), str(file2)]
    subprocess.run(cmd)

def parse_test_output(output, python_version):
    """
    Parse Python test suite output and structure the results
    
    Args:
        output (str): Raw output from test suite execution
        python_version (str): Version of Python being tested (e.g. "3.9.20")
        
    Returns:
        dict: Structured test results containing:
            - python_version: Version of Python tested
            - tests_run: Total number of tests executed
            - tests_failed: Number of failed/skipped tests
            - failed_tests: List of dicts with test details (name, error)
    """
    # Initialize results structure with default values
    results = {
        'python_version': python_version,
        'tests_run': 0,
        'tests_failed': 0,
        'failed_tests': []
    }
    
    # Process output line by line looking for test results
    lines = output.split('\n')
    for line in lines:
        # Look for lines containing test results (ok, FAIL, ERROR, or skipped)
        if 'test' in line and ('ok' in line or 'FAIL' in line or 'ERROR' in line or 'skipped' in line):
            results['tests_run'] += 1
            
            # Handle test failures and errors
            if 'FAIL' in line or 'ERROR' in line:
                results['tests_failed'] += 1
                results['failed_tests'].append({
                    'name': line.split(':')[0].strip() if ':' in line else line.strip(),
                    'error': line.strip()
                })
            
            # Handle skipped tests (counted as failures but marked differently)
            elif 'skipped' in line:
                results['tests_failed'] += 1
                results['failed_tests'].append({
                    'name': line.split(':')[0].strip() if ':' in line else line.strip(),
                    'error': f"{line.strip()} (skipped)"
                })
    
    # Fallback parsing if no standard test output format is found
    if results['tests_run'] == 0 and output.strip():
        # Use regex to find all test names in output
        test_pattern = r'test_[a-zA-Z0-9_]+'
        unique_tests = set(re.findall(test_pattern, output))
        results['tests_run'] = len(unique_tests)
        
        # Check each test for failure indicators
        for test in unique_tests:
            if f"{test} ... FAIL" in output or f"{test} ... ERROR" in output:
                results['tests_failed'] += 1
                results['failed_tests'].append({
                    'name': test,
                    'error': f"Test failed or had errors"
                })
    
    return results

def run_tests(python_path, output_dir):
    """
    Execute Python test suite and capture results
    
    Args:
        python_path (str): Path to Python executable
        output_dir (Path/str): Directory to store test results
        
    Returns:
        Path/None: Path to results JSON file if successful, None if failed
        
    Notes:
        - Creates timestamped JSON files for each test run
        - Includes basic test suite (int, float, bool, etc.)
        - Has 10-minute timeout for test execution
        - Captures both stdout and stderr
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get Python version and setup output file path
    python_version = subprocess.check_output([python_path, "-V"]).decode().split()[1]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = output_dir / f"test_results_{python_version}_{timestamp}.json"
    
    print(f"Running tests with {python_path}...")
    
    # Core test suite - fundamental Python functionality tests
    tests = [
        "test_int", "test_float", "test_bool", 
        "test_asyncio", "test_json", "test_struct", 
        "test_ctypes", "test_multiprocessing"
    ]
    
    try:
        # Execute test suite with verbose output
        cmd = [python_path, "-m", "test", "-v","-j0"] + tests
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 5 minute timeout
        )
        
        # Log execution results
        print(f"Return code: {result.returncode}")
        print(f"First 500 chars of stdout: {result.stdout[:500]}")
        print(f"First 500 chars of stderr: {result.stderr[:500]}")
        
        # Parse results and save to JSON
        test_results = parse_test_output(result.stdout, python_version)
        with open(output_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        return output_file
    except Exception as e:
        print(f"Error running tests: {e}")
        return None

def ensure_pyperf(python_path):
    try:
        subprocess.run([python_path, "-m", "pyperf", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print(f"Installing pyperf for {python_path}")
        subprocess.run([python_path, "-m", "pip", "install", "--user", "pyperf"], check=True)

def create_venv_if_needed(python_path):
    """Create and return path to a virtual environment for given Python"""
    venv_base = Path("venvs")
    venv_base.mkdir(exist_ok=True)
    python_name = os.path.basename(python_path)
    venv_path = venv_base / f"{python_name}-benchmark"
    
    if not venv_path.exists():
        print(f"Creating virtual environment for {python_name}")
        subprocess.run(
            [python_path, "-m", "venv", str(venv_path)],
            check=True
        )
    
    return venv_path

def install_in_venv(venv_path, packages):
    """Install packages in the specified virtual environment"""
    pip_path = venv_path / "bin" / "pip"
    for package in packages:
        print(f"Installing {package} in {venv_path.name}")
        subprocess.run(
            [str(pip_path), "install", "-q", package],
            check=True
        )

def get_venv_python(venv_path):
    """Get path to Python executable in virtual environment"""
    return str(venv_path / "bin" / "python")

def run_focused_comparison():
    """Run both test suite and performance comparisons for multiple Python versions"""
    python_versions = [
        "/opt/homebrew/bin/python3.9",
        "/opt/homebrew/bin/python3.10",
        "/opt/homebrew/bin/python3.11",
        "/opt/homebrew/bin/python3.12",
        "/opt/homebrew/bin/python3.13",
    ]
    
    output_dir = Path("comparison_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create comparison venv first (using first Python version)
    comparison_venv = create_venv_if_needed(python_versions[0])
    install_in_venv(comparison_venv, ["pyperf"])  # Only install pyperf in comparison venv
    
    # Run tests and benchmarks for each Python version
    test_results = []
    perf_results = []
    
    for python_path in python_versions:
        # Create venv for this Python version
        benchmark_venv = create_venv_if_needed(python_path)
        install_in_venv(benchmark_venv, ["pyperformance"])  # Only install pyperformance
        
        venv_python = get_venv_python(benchmark_venv)
        
        # Run tests and benchmarks using venv Python
        print(f"\n=== Running tests and benchmarks for {python_path} ===")
        test_result = run_tests(venv_python, output_dir)
        if test_result:
            test_results.append(test_result)
        
        perf_result = run_benchmark(venv_python, output_dir)
        if perf_result:
            perf_results.append(perf_result)
    
    # Generate reports
    if len(test_results) >= 2:
        print("\n=== Test Suite Comparison Results ===")
        test_report = generate_test_comparison_report(test_results, output_dir)
        print(f"Test comparison report: {test_report}")

    if len(perf_results) >= 2:
        print("\n=== Performance Comparison Results ===")
        comparison_python = get_venv_python(comparison_venv)
        
        # Do pairwise comparisons using the comparison venv
        for i in range(len(perf_results)-1):
            print(f"\nComparing {Path(perf_results[i]).name} vs {Path(perf_results[i+1]).name}:")
            subprocess.run([
                comparison_python,  # Use the venv Python with pyperf installed
                "-m", "pyperf", "compare_to",
                "--table", str(perf_results[i]), str(perf_results[i+1])
            ], check=True)

    print("\nComparison complete. Results are in the 'comparison_results' directory.")

if __name__ == "__main__":
    run_focused_comparison()