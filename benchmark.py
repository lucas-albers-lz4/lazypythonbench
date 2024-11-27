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

def run_benchmark(python_path, output_dir):
    """Run minimal benchmarks for testing report generation"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    python_version = subprocess.check_output([python_path, "-V"]).decode().split()[1]
    output_file = output_dir / f"python{python_version}_{timestamp}.json"
    
    # Set environment variables to suppress pip warnings and virtualenv output
    env = os.environ.copy()
    env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    env['PYTHONWARNINGS'] = 'ignore:DEPRECATION'
    env['VIRTUALENV_NO_PERIODIC_UPDATE'] = '1'
    env['PIP_QUIET'] = '1'  # Added to reduce pip output
    env['VIRTUALENV_QUIET'] = '1'  # Added to reduce virtualenv output
    
    # Minimal set of fast benchmarks with reduced iterations
    cmd = [
        python_path, "-m", "pyperformance", "run",
        "--python", python_path,
        "--benchmarks", "json_dumps,richards",  # Just two fast benchmarks
        "--fast",  # Reduce number of iterations
        "--output", str(output_file),
        "--inherit-environ", "PIP_DISABLE_PIP_VERSION_CHECK,PYTHONWARNINGS,VIRTUALENV_NO_PERIODIC_UPDATE,PIP_QUIET,VIRTUALENV_QUIET"
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

def run_python_tests(python_path, output_dir):
    """Run Python test suite with specified Python version."""
    cmd = [
        python_path, 
        "-m", 
        "test",
        "test_asyncio",
        "test_json",
        "test_struct",
        "test_ctypes",
        "test_multiprocessing",
        "-v",
        "-j8",
        "--timeout=300"
    ]
    
    try:
        print(f"Running tests with {python_path}...")
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            check=False
        )
        
        # Add diagnostic output
        print(f"Return code: {result.returncode}")
        print("First 500 chars of stdout:", result.stdout[:500])
        print("First 500 chars of stderr:", result.stderr[:500])
        
        if result.returncode == 0:
            print("Tests completed successfully")
        else:
            print("Tests completed with failures")
            
        return parse_test_results(result)
    except Exception as e:
        print(f"Error running tests: {e}")
        return None

def parse_test_results(result):
    """Parse test results from subprocess output."""
    version = re.search(r'CPython ([\d.]+)', result.stdout)
    if not version:
        return None
        
    version = version.group(1)
    
    # Initialize counters
    tests_run = 0
    tests_failed = 0
    failed_tests = []
    
    # Parse test failures
    for line in result.stdout.split('\n') + result.stderr.split('\n'):
        if 'test_' in line and 'failed' in line.lower():
            tests_failed += 1
            test_name = re.search(r'test_\w+', line)
            if test_name:
                failed_tests.append({
                    'name': test_name.group(),
                    'error': line.strip()
                })
    
    # Count total tests from the "Run X tests" line
    run_tests_match = re.search(r'Run (\d+) tests?', result.stdout)
    if run_tests_match:
        tests_run = int(run_tests_match.group(1))
    else:
        # Fallback: count the number of test_* mentions that aren't failures
        tests_run = len(re.findall(r'test_\w+(?!.*failed)', result.stdout))
    
    return {
        'python_version': version,
        'tests_run': tests_run,
        'tests_passed': max(0, tests_run - tests_failed),  # Ensure non-negative
        'tests_failed': tests_failed,
        'failed_tests': failed_tests,
        'return_code': result.returncode
    }

def ensure_pyperf(python_path):
    try:
        subprocess.run([python_path, "-m", "pyperf", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print(f"Installing pyperf for {python_path}")
        subprocess.run([python_path, "-m", "pip", "install", "--user", "pyperf"], check=True)

def run_focused_comparison():
    """Run both test suite and performance comparisons for multiple Python versions"""
    python_versions = [
        "/opt/homebrew/bin/python3.9",
        "/opt/homebrew/bin/python3.10",
        "/opt/homebrew/bin/python3.11",
    ]
    
    output_dir = Path("comparison_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Run Python test suite comparisons
    print("\n=== Running Python Test Suite Comparisons ===")
    test_results = []
    for python_path in python_versions:
        result = run_python_tests(python_path, output_dir)
        if result:
            # Save result to file
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            result_file = output_dir / f"test_results_{result['python_version']}_{timestamp}.json"
            with open(result_file, 'w') as f:
                json.dump(result, f)
            test_results.append(result_file)
    
    print(f"Number of test results: {len(test_results)}")
    for result in test_results:
        print(f"Test result file: {result}")
    
    # 2. Run Performance comparisons
    print("\n=== Running Performance Comparisons ===")
    perf_results = []
    for python_path in python_versions:
        ensure_requirements(python_path)
        result_file = run_benchmark(python_path, output_dir)
        if result_file:
            perf_results.append(result_file)
    
    # Generate reports
    if len(test_results) >= 2:
        print("\n=== Test Suite Comparison Results ===")
        test_report = generate_test_comparison_report(test_results, output_dir)
        print(f"Test comparison report: {test_report}")

    if len(perf_results) >= 2:
        print("\n=== Performance Comparison Results ===")
        # Do pairwise comparisons
        ensure_pyperf(python_versions[0])
        for i in range(len(perf_results)-1):
            print(f"\nComparing {Path(perf_results[i]).name} vs {Path(perf_results[i+1]).name}:")
            # Generate table comparison using python -m to ensure we use the correct pyperf
            subprocess.run([
                python_versions[0],  # Use the first Python executable
                "-m", "pyperf", "compare_to",
                "--table", str(perf_results[i]), str(perf_results[i+1])
            ], check=True)

    print("\nComparison complete. Results are in the 'comparison_results' directory.")

if __name__ == "__main__":
    run_focused_comparison()