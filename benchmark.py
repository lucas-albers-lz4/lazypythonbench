#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json
import os
from tabulate import tabulate

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
    
    # Set environment variables to suppress pip warnings
    env = os.environ.copy()
    env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    env['PYTHONWARNINGS'] = 'ignore:DEPRECATION'
    env['VIRTUALENV_NO_PERIODIC_UPDATE'] = '1'
    
    # Minimal set of fast benchmarks with reduced iterations
    cmd = [
        python_path, "-m", "pyperformance", "run",
        "--python", python_path,
        "--benchmarks", "json_dumps,richards",  # Just two fast benchmarks
        "--fast",  # Reduce number of iterations
        "--output", str(output_file),
        "--inherit-environ", "PIP_DISABLE_PIP_VERSION_CHECK,PYTHONWARNINGS,VIRTUALENV_NO_PERIODIC_UPDATE"
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
    headers = ["Python Version", "Tests Run", "Failed"]
    table_data = [
        [r['python_version'], r['tests_run'], r['tests_failed']]
        for r in results
    ]
    
    with open(report_file, 'w') as f:
        # Main summary with tabulate
        f.write("# Python Test Suite Comparison Report\n\n")
        f.write(tabulate(table_data, headers=headers, tablefmt="pipe", numalign="right"))
        f.write("\n\n")  # Extra newlines for markdown spacing
        
        # Failed Tests by Version
        f.write("## Failed Tests by Version\n\n")
        has_failures = False
        for result in results:
            if result['failed_tests']:
                has_failures = True
                f.write(f"### Python {result['python_version']}\n")
                for test in result['failed_tests']:
                    f.write(f"- {test}\n")
        
        if not has_failures:
            f.write("*No test failures in any version*\n")
        
        # Failure Differences
        f.write("\n## Failure Differences Between Versions\n\n")
        base = results[0]
        base_failures = set(base['failed_tests'])
        
        for current in results[1:]:
            current_failures = set(current['failed_tests'])
            
            f.write(f"### {base['python_version']} → {current['python_version']}\n\n")
            
            if not base_failures and not current_failures:
                f.write("*No differences in test failures*\n\n")
                continue
                
            # New failures
            new_failures = current_failures - base_failures
            if new_failures:
                f.write("New failures:\n")
                for failure in sorted(new_failures):
                    f.write(f"- {failure}\n")
            
            # Fixed failures
            fixed_failures = base_failures - current_failures
            if fixed_failures:
                f.write("\nFixed in new version:\n")
                for failure in sorted(fixed_failures):
                    f.write(f"- {failure}\n")
            
            f.write("\n")
    
    print(f"\nTest comparison report saved to: {report_file}")
    return report_file

def compare_results(file1, file2):
    """Compare two benchmark result files using pyperf"""
    cmd = ["python3.9", "-m", "pyperf", "compare", str(file1), str(file2)]
    subprocess.run(cmd)

def run_python_tests(python_path, output_dir):
    """Run Python test suite and save results"""
    cmd = [
        python_path, 
        "-m", "test",
        "test_int",
        "test_float", 
        "test_bool",
        "test_asyncio",
        "test_json",
        "test_struct",
        "test_ctypes",
        "test_multiprocessing",
        "-j8"   # Reduced parallelism
        "--timeout=300"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return parse_test_results(result)
    except subprocess.CalledProcessError as e:
        print(f"Error running tests: {e}")
        print(f"Output: {e.output}")
        return None

def parse_test_results(result):
    """Parse the test results from subprocess output."""
    # Get Python version from the command used to run the test
    python_path = result.args[0]
    python_version = subprocess.check_output([python_path, "-V"]).decode().split()[1]
    
    if result.returncode != 0:
        print("Tests failed to run successfully.")
        return {
            "python_version": python_version,
            "tests_run": 0,
            "tests_failed": 2,  # Indicating failure state
            "failed_tests": []
        }
    
    parsed_results = {
        "python_version": python_version,
        "tests_run": 0,
        "tests_failed": 0,
        "failed_tests": []
    }
    
    for line in result.stdout.splitlines():
        if "Ran" in line and "tests" in line:
            try:
                parsed_results["tests_run"] = int(line.split()[1])
            except (ValueError, IndexError):
                continue
        elif "FAILED" in line:
            parsed_results["tests_failed"] += 1
            parsed_results["failed_tests"].append(line.strip())
    
    return parsed_results

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
        result_file = run_python_tests(python_path, output_dir)
        if result_file:
            test_results.append(result_file)
    
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
        for i in range(len(perf_results)-1):
            print(f"\nComparing {Path(perf_results[i]).name} vs {Path(perf_results[i+1]).name}:")
            # Generate table comparison
            subprocess.run([
                "python3.9", "-m", "pyperf", "compare_to", 
                "--table", 
                str(perf_results[i]), 
                str(perf_results[i+1])
            ])
        
        # Generate stats for each result
        for result in perf_results:
            print(f"\nStats for {result.name}:")
            subprocess.run([
                "python3.9", "-m", "pyperf", "stats",
                str(result)
            ])

if __name__ == "__main__":
    run_focused_comparison()