#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json
import os
from tabulate import tabulate
import re
import argparse
import platform
import psutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict
import time

# Constants
BREWPATH = "/opt/homebrew/bin/"
PYTHON_BASE_VERSIONS = [
    "3.12",
    "3.13",
    ]
python_versions = [f"{BREWPATH}python{version}" for version in PYTHON_BASE_VERSIONS]

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

def check_system_settings_macos():
    """
    Check system settings that could impact benchmark accuracy on macOS.
    Returns (bool, list): Tuple of (is_suitable, list_of_issues)
    """
    issues = []
    
    try:
        # Check power source
        power_source = subprocess.check_output(['pmset', '-g', 'ps']).decode()
        if "Battery Power" in power_source:
            issues.append("Running on battery power (may affect performance)")
        else:
            print("✓ Power source: AC power")
            
        # Memory check using psutil
        memory = psutil.virtual_memory()
        available_memory_gb = memory.available / (1024 * 1024 * 1024)
        total_memory_gb = memory.total / (1024 * 1024 * 1024)
        min_required_gb = total_memory_gb * 0.25
        
        if available_memory_gb < min_required_gb:
            issues.append(f"Low available memory: {available_memory_gb:.1f}GB available (need at least {min_required_gb:.1f}GB)")
        else:
            print(f"✓ Memory: {available_memory_gb:.1f}GB available")
            
        # Check Spotlight indexing - look for active mdworker CPU usage
        ps_output = subprocess.check_output(['ps', '-eo', 'pcpu,comm'], text=True).splitlines()
        spotlight_processes = [line for line in ps_output if 'mdworker' in line]
        active_indexing = any(float(proc.split()[0]) > 0.5 for proc in spotlight_processes)
        
        if active_indexing:
            issues.append("Spotlight indexing is active (mdworker using CPU)")
        else:
            print("✓ Spotlight: No active indexing")
            
        # Check Time Machine
        if 'com.apple.backupd' in subprocess.check_output(['ps', 'aux']).decode():
            issues.append("Time Machine backup in progress")
        else:
            print("✓ Time Machine: No backup in progress")
            
    except subprocess.CalledProcessError as e:
        issues.append(f"Unable to check system settings: {e}")
    except Exception as e:
        issues.append(f"Error checking system settings: {e}")
        
    return len(issues) == 0, issues

def check_system_settings():
    """Platform-aware system settings check"""
    if platform.system() == 'Darwin':  # macOS
        return check_system_settings_macos()
    else:
        print("System checks are currently only implemented for macOS")
        return True, []  # Allow benchmarks to proceed on other platforms

def run_benchmark(python_path, output_dir, bench_scope="default"):
    """Run benchmarks for testing report generation
    
    Args:
        python_path (str): Path to Python executable
        output_dir (Path/str): Directory to store benchmark results
        bench_scope (str): One of "quick", "default", or "full" to determine benchmark scope
        
    Returns:
        Path/None: Path to benchmark results file if successful, None if failed
        
    Notes:
        - Checks system settings before running benchmarks
        - Creates timestamped JSON file for results
        - Runs benchmarks based on scope:
          * quick: only pyflate benchmark
          * default: uses pyperformance's default benchmark group
          * full: runs all available benchmarks (-b all)
        - Uses quiet environment settings to reduce output noise
    """
    # First check system settings with retries
    print("\nChecking system settings for benchmark suitability...")
    max_attempts = 20
    delay_seconds = 30
    
    for attempt in range(max_attempts):
        is_suitable, issues = check_system_settings()
        
        if is_suitable:
            print("✓ System settings suitable for benchmarking")
            break
            
        if attempt < max_attempts - 1:
            print(f"\n⚠️  Attempt {attempt + 1}/{max_attempts}: System not ready:")
            for issue in issues:
                print(f"  • {issue}")
            print(f"\nWaiting {delay_seconds} seconds before next check...")
            time.sleep(delay_seconds)
        else:
            print("\n❌ Maximum attempts reached. System settings are not suitable:")
            for issue in issues:
                print(f"  • {issue}")
            print("\nPlease resolve these issues and try again.")
            print("(To bypass this check, use --disable-system-check)")
            return None
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    python_version = subprocess.check_output([python_path, "-V"]).decode().split()[1]
    output_file = output_dir / f"python{python_version}_{timestamp}.json"
    
    # Common environment variables for suppressing output
    QUIET_ENV = {
        'PIP_DISABLE_PIP_VERSION_CHECK': '1',    # Prevents pip from checking for newer versions of itself
        'PYTHONWARNINGS': 'ignore',              # Suppresses all Python warnings
        'VIRTUALENV_NO_PERIODIC_UPDATE': '1',     # Prevents virtualenv from checking for updates
        'PIP_QUIET': '1',                        # Reduces pip output to essential messages only
        'VIRTUALENV_QUIET': '1',                 # Suppresses virtualenv creation messages
        'PIP_NO_INPUT': '1',                     # Prevents pip from asking for user input
        'PIP_PROGRESS_BAR': 'off',               # Disables progress bar in pip installations
        'PIP_NO_COLOR': '1',                     # Disables colored output in pip
        'PYPERFORMANCE_QUIET': '1',              # Suppresses pyperformance benchmark output
        'VIRTUALENV_VERBOSE': '0',               # Sets virtualenv verbosity to minimum
        'PIP_VERBOSE': '0',                      # Sets pip verbosity to minimum
        'PYPERFORMANCE_SYSTEM_TUNE': '0',        # Disables system tuning during benchmarks
        'PIP_LOG_LEVEL': 'ERROR',                # Sets pip logging to show only errors
        'PYTHONUNBUFFERED': '1',                 # Disables Python output buffering
        'PYPERFORMANCE_VERBOSE': '0',            # Reduces pyperformance verbosity
        'PIP_NO_CACHE_DIR': 'off',               # Controls pip's cache behavior (allows caching)
        'VIRTUALENV_NO_DOWNLOAD': '1',           # Prevents virtualenv from downloading updates
        'VIRTUALENV_CLEAR': '1'                  # Clears existing virtualenv on creation
    }
    
    # Set environment variables
    env = os.environ.copy()
    env.update(QUIET_ENV)
    
    cmd = [
        python_path, "-m", "pyperformance", "run",
        "--python", python_path,
        "--output", str(output_file),
        "--inherit-environ", ",".join(QUIET_ENV.keys())
    ]
    
    # Only add benchmark specification if not using defaults
    if bench_scope == "quick":
        cmd.extend(["--benchmarks", "pyflate"])
    elif bench_scope == "full":
        cmd.extend(["--benchmarks", "all"])
    # For "default", we don't specify any benchmarks to use pyperformance's defaults
    
    try:
        print(f"\nRunning {bench_scope} benchmarks with {python_path}...")
        subprocess.run(cmd, env=env, check=True)
        print(f"Benchmark results saved to: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error running benchmarks: {e}")
        return None

def generate_test_comparison_report(files, output_dir):
    """Generate a focused comparison report of test failures"""
    print("\n=== Debug: Test Files Content ===")
    print(f"Number of files to process: {len(files)}")
    
    report_file = output_dir / f"test_comparison_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"
    print(f"\nGenerating report at: {report_file}")
    
    results = []
    for file in files:
        print(f"Processing file: {file} (type: {type(file)})")
        with open(file) as test_file:
            data = json.load(test_file)
            print(f"Loaded JSON data keys: {data.keys()}")
            results.append(data)
    
    # Prepare table data with debug output
    headers = ["Python Version", "Tests Run", "Passed", "Failed", "Skipped"]
    print("\n=== Preparing Table Data ===")
    table_data = [
        [
            r['python_version'], 
            r['tests_run'], 
            r['tests_run'] - r['tests_failed'] - r['tests_skipped'],
            r['tests_failed'],
            r['tests_skipped']
        ]
        for r in results
    ]
    print(f"Table data prepared: {len(table_data)} rows")
    
    with open(report_file, 'w') as f:
        # Main summary with tabulate
        f.write("# Python Test Suite Comparison Report\n\n")
        f.write(tabulate(table_data, headers=headers, tablefmt="pipe", numalign="right"))
        f.write("\n\n")
        
        # Failed and Skipped Tests by Version
        f.write("## Failed and Skipped Tests by Version\n\n")
        has_issues = False
        for result in results:
            if result['failed_tests'] or result['skipped_tests']:
                has_issues = True
                f.write(f"### Python {result['python_version']}\n")
                if result['failed_tests']:
                    f.write("#### Failed:\n")
                    for test in result['failed_tests']:
                        f.write(f"- {test['name']}: {test['error']}\n")
                if result['skipped_tests']:
                    f.write("#### Skipped:\n")
                    for test in result['skipped_tests']:
                        f.write(f"- {test['name']}: {test['error']}\n")
                f.write("\n")
        if not has_issues:
            f.write("*No test failures or skips in any version*\n\n")
        
        # Tests Failing in All Versions
        f.write("## Tests Failing in All Versions\n\n")
        all_failures = [set((test['name'], test['error']) for test in result['failed_tests']) for result in results]
        common_failures = set.intersection(*all_failures) if all_failures else set()
        
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
        'tests_skipped': 0,
        'failed_tests': [],
        'skipped_tests': []
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
            
            # Handle skipped tests separately
            elif 'skipped' in line:
                results['tests_skipped'] += 1
                results['skipped_tests'].append({
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

def run_tests(python_path, output_dir, quick_mode=False):
    """
    Execute Python test suite and capture results
    
    Args:
        python_path (str): Path to Python executable
        output_dir (Path/str): Directory to store test results
        quick_mode (bool): If True, runs only core functionality tests
        
    Returns:
        Path/None: Path to results JSON file if successful, None if failed
        
    Notes:
        - Creates timestamped JSON and XML files for each test run
        - JSON used for report generation and comparisons
        - XML available for detailed test analysis
        - Uses parallel execution (-j0) for both quick and full modes
        - Runs core functionality tests only if quick_mode is True
        - Has 10-minute timeout for test execution
        - Captures both stdout and stderr
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    python_version = subprocess.check_output([python_path, "-V"]).decode().split()[1]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = output_dir / f"test_results_{python_version}_{timestamp}.json"
    xml_file = output_dir / f"test_results_{python_version}_{timestamp}.xml"
    
    print(f"Running tests with {python_path}...")
    
    try:
        # Minimal environment variables needed to suppress crash dialogs on macOS
        env = os.environ.copy()
        env.update({
            'CrashReporterDisabled': '1',
            'NSDocumentRevisionsDebugMode': 'TRUE'
        })
        
        # Base command with common options
        cmd = [
            python_path, 
            "-m", 
            "test",
            "-j0",                        # parallel execution
            f"--junit-xml={xml_file}"    # XML output for reports
        ]
        
        if quick_mode:
            # Directly specify test names as arguments
            quick_tests = [
                "test_int",
                "test_float",
                "test_bool", 
                "test_asyncio",
                "test_json",
                "test_struct", 
                "test_ctypes"
            ]
            cmd.extend(quick_tests)
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        # Log execution results
        print(f"Return code: {result.returncode}")
        print(f"First 500 chars of stdout: {result.stdout[:500]}")
        print(f"First 500 chars of stderr: {result.stderr[:500]}")
        
        # Parse results and save to JSON
        test_results = parse_test_output(result.stdout, python_version)
        with open(output_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"Test results saved to:\n  JSON: {output_file}\n  XML: {xml_file}")
        
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

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run Python version comparisons')
    parser.add_argument('--disable-test', action='store_true',
                      help='Skip running unit tests and test comparison')
    parser.add_argument('--disable-benchmark', action='store_true',
                      help='Skip running performance benchmarks')
    parser.add_argument('--disable-system-check', action='store_true',
                      help='Skip system suitability check before benchmarking')
    
    # Benchmark scope group (mutually exclusive)
    benchmark_scope = parser.add_mutually_exclusive_group()
    benchmark_scope.add_argument("--bench-quick", action="store_true",
                               help="Run only pyflate benchmark (fastest)")
    benchmark_scope.add_argument("--bench-default", action="store_true",
                               help="Run default benchmark group (default)")
    benchmark_scope.add_argument("--bench-full", action="store_true",
                               help="Run all available benchmarks (slowest)")
    
    # Preserve existing quick mode and unittest report flags
    parser.add_argument('--quick', action='store_true',
                      help='Run minimal set of tests (does not affect benchmarks)')
    parser.add_argument('--unittest-report', action='store_true',
                      help='Generate unit test comparison report from existing files without running tests')
    
    return parser.parse_args()

def validate_and_compare_test_files(json_files, xml_files):
    """Compare test counts between JSON and XML files"""
    results = {}
    
    # Process JSON files
    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)
            version = data['python_version']
            results[version] = {'json': data}

    # Process XML files
    for xml_file in xml_files:
        version = xml_file.stem.split('_')[2]  # Assuming version is in the filename
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        xml_data = {
            'total_tests': int(root.get('tests', 0)),
            'errors': int(root.get('errors', 0)),
            'failures': int(root.get('failures', 0)),
            'skipped': sum(1 for _ in root.findall('.//skipped'))
        }
        results[version]['xml'] = xml_data

    # Print comparison
    print("\nVersion by Version Comparison:")
    print("-" * 80)
    for version in sorted(results.keys()):
        print(f"\nPython {version}:")
        json_data = results[version]['json']
        xml_data = results[version]['xml']
        
        print("  JSON Counts:")
        print(f"    Tests Run: {json_data.get('tests_run', 'N/A')}")
        print(f"    Tests Failed: {json_data.get('tests_failed', 'N/A')}")
        print(f"    Tests Skipped: {json_data.get('tests_skipped', 'N/A')}")
        print(f"    Failed Tests List Length: {len(json_data.get('failed_tests', []))}")
        print(f"    Skipped Tests List Length: {len(json_data.get('skipped_tests', []))}")
        
        print("  XML Counts:")
        print(f"    Total Tests: {xml_data.get('total_tests', 'N/A')}")
        print(f"    Errors: {xml_data.get('errors', 'N/A')}")
        print(f"    Failures: {xml_data.get('failures', 'N/A')}")
        print(f"    Skipped: {xml_data.get('skipped', 'N/A')}")
        
        # Calculate and show discrepancies
        if json_data and xml_data:
            print("  Discrepancies:")
            print(f"    Tests Run vs Total Tests: {json_data['tests_run']} vs {xml_data['total_tests']}")
            print(f"    Failed Tests: {json_data['tests_failed']} vs {xml_data['failures'] + xml_data['errors']}")
            print(f"    Skipped Tests: {json_data['tests_skipped']} vs {xml_data['skipped']}")
    
    return results

def run_focused_comparison():
    """Main function to run the focused comparison"""
    args = parse_arguments()
    
    output_dir = Path("benchmark_results")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.unittest_report:
        json_files = sorted(output_dir.glob('test_results_*.json'))
        xml_files = sorted(output_dir.glob('test_results_*.xml'))
        
        # Generate the new comprehensive version comparison report
        report_file = generate_version_comparison_report(json_files, xml_files, output_dir)
        print(f"\nGenerated comprehensive unittest comparison report: {report_file}")
        
        # If there are any existing unittest report generation code, keep it here
        validate_and_compare_test_files(json_files, xml_files)
        return report_file

    # Only check system settings once at start if we're running benchmarks and checks aren't disabled
    if not args.disable_benchmark and not args.disable_system_check:
        print("\nChecking system settings for benchmark suitability...")
        is_suitable, issues = check_system_settings_macos()
        if not is_suitable:
            print("\n❌ Benchmark aborted. System settings are not suitable:")
            for issue in issues:
                print(f"  • {issue}")
            print("\nPlease resolve these issues and try again.")
            print("(To bypass this check, use --disable-system-check)")
            return
        print("\n✓ System ready for benchmarking\n")
    
    test_results = []
    perf_results = []
    
    # Only create comparison venv if benchmarks are enabled
    comparison_venv = None
    if not args.disable_benchmark:
        comparison_venv = create_venv_if_needed(python_versions[0])
        install_in_venv(comparison_venv, ["pyperf"])
    
    for python_path in python_versions:
        benchmark_venv = None
        venv_python = None
        
        # Create venv based on what we're running
        if not args.disable_benchmark:
            benchmark_venv = create_venv_if_needed(python_path)
            install_in_venv(benchmark_venv, ["pyperformance"])
            venv_python = get_venv_python(benchmark_venv)
        elif not args.disable_test:
            # We still need a venv for tests
            benchmark_venv = create_venv_if_needed(python_path)
            venv_python = get_venv_python(benchmark_venv)
            
        print(f"\n=== Processing {python_path} ===")
        
        # Run tests if enabled (preserving existing quick mode for tests)
        if not args.disable_test:
            test_result = run_tests(venv_python, output_dir, quick_mode=args.quick)
            if test_result:
                test_results.append(test_result)
        
        # Run benchmarks if enabled (using updated bench scope)
        if not args.disable_benchmark:
            bench_scope = "quick" if args.bench_quick else "full" if args.bench_full else "default"
            perf_result = run_benchmark(venv_python, output_dir, bench_scope=bench_scope)
            if perf_result:
                perf_results.append(perf_result)
    
    # Generate test report if tests were run and we have results
    if not args.disable_test and len(test_results) >= 2:
        print("\n=== Test Suite Comparison Results ===")
        test_report = generate_test_comparison_report(test_results, output_dir)
        print(f"Test comparison report: {test_report}")

    # Run benchmark comparisons if benchmarks were run and we have results
    if not args.disable_benchmark and len(perf_results) >= 2:
        print("\n=== Performance Comparison Results ===")
        comparison_python = get_venv_python(comparison_venv)
        
        # Generate markdown report comparing all versions at once
        report_file = output_dir / f"benchmark_comparison_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"
        with open(report_file, 'w') as f:
            f.write("# Python Performance Comparison\n\n")
            f.write("## System Information\n")
            f.write("```\n")
            # Add system info - 'show' is the correct subcommand
            subprocess.run([
                comparison_python, "-m", "pyperf", "system", "show"
            ], stdout=f, check=True)
            f.write("```\n\n")
            
            f.write("## Benchmark Results\n")
            f.write("```\n")
            # Fixed command: changed 'compare' to 'compare_to' and moved --table to end
            subprocess.run([
                comparison_python, "-m", "pyperf", "compare_to",
                *[str(result) for result in perf_results],
                "--table","--table-format","md"
            ], stdout=f, check=True)
            f.write("```\n")
        print(f"\nMarkdown comparison report generated: {report_file}")

    print("\nComparison complete. Results are in the 'benchmark_results' directory.")

def parse_xml_test_results(xml_file):
    """Parse XML test results and extract test count information"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Extract test suite attributes
        total_tests = int(root.get('tests', 0))
        errors = int(root.get('errors', 0))
        failures = int(root.get('failures', 0))
        
        # Count skipped tests
        skipped_tests = len(root.findall(".//testcase[@status='skipped']"))
        
        return {
            'total_tests': total_tests,
            'errors': errors,
            'failures': failures,
            'skipped_tests': skipped_tests
        }
    except Exception as e:
        print(f"Error parsing XML file {xml_file}: {e}")
        return None

def validate_test_result_json(file_path):
    """Validate JSON test result file structure and content"""
    try:
        with open(file_path) as f:
            data = json.load(f)
        
        required_fields = [
            'python_version', 'tests_run', 'tests_failed', 
            'tests_skipped', 'failed_tests', 'skipped_tests'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
            
        if not isinstance(data['python_version'], str):
            return False, "python_version must be string"
        if not isinstance(data['tests_run'], int):
            return False, "tests_run must be integer"
        if not isinstance(data['tests_failed'], int):
            return False, "tests_failed must be integer"
        if not isinstance(data['tests_skipped'], int):
            return False, "tests_skipped must be integer"
        if not isinstance(data['failed_tests'], list):
            return False, "failed_tests must be list"
        if not isinstance(data['skipped_tests'], list):
            return False, "skipped_tests must be list"
            
        total = data['tests_failed'] + data['tests_skipped']
        if total > data['tests_run']:
            return False, "Failed + skipped tests exceed total tests run"
            
        return True, "Valid"
        
    except json.JSONDecodeError:
        return False, "Invalid JSON format"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def validate_test_result_xml(file_path):
    """Validate XML test result file structure and content"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        if root.tag != 'testsuites' and root.tag != 'testsuite':
            return False, "Root element must be 'testsuites' or 'testsuite'"
        
        required_attrs = ['tests', 'errors', 'failures']
        
        missing_attrs = [attr for attr in required_attrs if root.get(attr) is None]
        if missing_attrs:
            return False, f"Missing required attributes: {', '.join(missing_attrs)}"
            
        for attr in required_attrs:
            try:
                int(root.get(attr))
            except ValueError:
                return False, f"Attribute '{attr}' must be an integer"
                
        testcases = root.findall(".//testcase")
        if not testcases:
            return False, "No testcase elements found"
            
        return True, "Valid"
        
    except ET.ParseError:
        return False, "Invalid XML format"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def generate_version_comparison_report(json_files, xml_files, output_dir):
    """Generate a comprehensive report comparing XML and JSON test results for each Python version"""
    
    results_by_version = {}
    
    # First, organize files by Python version
    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)
            version = data['python_version']
            if version not in results_by_version:
                results_by_version[version] = {'json': data}
    
    for xml_file in xml_files:
        version = xml_file.stem.split('_')[2]  # Assuming version is in filename
        if version in results_by_version:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Extract XML metrics
            xml_data = {
                'total_tests': int(root.get('tests', 0)),
                'total_errors': int(root.get('errors', 0)),
                'total_failures': int(root.get('failures', 0)),
                'skipped_tests': sum(1 for _ in root.findall('.//skipped')),
                'failures': extract_failures(root),  # Add detailed failure information
                'file_metrics': {
                    'total_files': 0,
                    'files_run': 0,
                    'files_failed': 0,
                    'files_skipped': 0,
                    'resource_denied': 0
                }
            }
            
            # Extract file metrics from the final summary in XML
            for testcase in root.findall('.//testcase'):
                if 'Total test files' in testcase.get('name', ''):
                    error_text = testcase.find('error').text if testcase.find('error') else ''
                    if error_text:
                        # Parse metrics from error text
                        matches = re.findall(r'run=(\d+)/(\d+) failed=(\d+) skipped=(\d+) resource_denied=(\d+)', error_text)
                        if matches:
                            run, total, failed, skipped, denied = map(int, matches[0])
                            xml_data['file_metrics'].update({
                                'total_files': total,
                                'files_run': run,
                                'files_failed': failed,
                                'files_skipped': skipped,
                                'resource_denied': denied
                            })
            
            results_by_version[version]['xml'] = xml_data
    
    # Generate report
    report_file = output_dir / f"version_comparison_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"
    
    with open(report_file, 'w') as f:
        f.write("# Python Version Test Results Comparison\n\n")
        
        for version in sorted(results_by_version.keys()):
            data = results_by_version[version]
            f.write(f"## Python {version}\n\n")
            
            # JSON Results Section
            f.write("### JSON Format Results\n")
            json_data = data['json']
            f.write("```python\n")
            f.write("Primary Metrics:\n")
            f.write(f"- Tests Run: {json_data['tests_run']}\n")
            f.write(f"- Tests Failed: {json_data['tests_failed']}\n")
            f.write(f"- Tests Skipped: {json_data['tests_skipped']}\n")
            success_rate = 100 * (json_data['tests_run'] - json_data['tests_failed']) / json_data['tests_run'] if json_data['tests_run'] > 0 else 0
            f.write(f"- Success Rate: {success_rate:.2f}%\n\n")
            
            # Group skipped tests by category
            skip_categories = {
                'Platform Dependencies': [],
                'Resource Dependencies': [],
                'Missing Modules': [],
                'Build/Environment': []
            }
            
            for skip in json_data['skipped_tests']:
                error = skip['error'].lower()
                if any(x in error for x in ['windows', 'android', 'macos']):
                    skip_categories['Platform Dependencies'].append(skip['name'])
                elif any(x in error for x in ['network', 'audio', 'cpu']):
                    skip_categories['Resource Dependencies'].append(skip['name'])
                elif 'no module' in error:
                    skip_categories['Missing Modules'].append(skip['name'])
                else:
                    skip_categories['Build/Environment'].append(skip['name'])
            
            f.write("Skip Categories:\n")
            for category, tests in skip_categories.items():
                if tests:
                    f.write(f"{category}: {len(tests)} tests\n")
            f.write("```\n\n")
            
            # Updated XML Results Section
            if 'xml' in data:
                f.write("### XML Format Results\n")
                xml_data = data['xml']
                f.write("```python\n")
                f.write("Primary Metrics:\n")
                f.write(f"- Total Tests: {xml_data['total_tests']}\n")
                f.write(f"- Total Errors: {xml_data['total_errors']}\n")
                f.write(f"- Total Failures: {xml_data['total_failures']}\n")
                f.write(f"- Total Skipped: {xml_data['skipped_tests']}\n")
                success_rate = 100 * (xml_data['total_tests'] - xml_data['total_errors'] - xml_data['total_failures']) / xml_data['total_tests']
                f.write(f"- Success Rate: {success_rate:.2f}%\n\n")
                
               
            
            # Format Comparison Section
            f.write("### Format Comparison\n")
            f.write("- XML provides detailed test execution metrics at both file and test level\n")
            f.write("- JSON provides high-level suite results with detailed skip information\n")
            f.write("- Skip patterns show correlation between resource denials and specific skip reasons\n\n")
            
            f.write("---\n\n")
        
        # Add Summary Tables at the end
        f.write("\n## Summary Comparison Tables\n\n")
        
        # Prepare JSON Results Summary Table data
        json_headers = ["Python Version", "Tests Run", "Tests Failed", "Tests Skipped", "Success Rate", 
                       "Platform Deps", "Resource Deps", "Missing Modules", "Build/Env"]
        json_table_data = []
        
        for version in sorted(results_by_version.keys(), reverse=True):
            data = results_by_version[version]['json']
            success_rate = 100 * (data['tests_run'] - data['tests_failed']) / data['tests_run'] if data['tests_run'] > 0 else 0
            
            # Count skip categories
            skip_categories = {
                'Platform Dependencies': 0,
                'Resource Dependencies': 0,
                'Missing Modules': 0,
                'Build/Environment': 0
            }
            
            for skip in data['skipped_tests']:
                error = skip['error'].lower()
                if any(x in error for x in ['windows', 'android', 'macos']):
                    skip_categories['Platform Dependencies'] += 1
                elif any(x in error for x in ['network', 'audio', 'cpu']):
                    skip_categories['Resource Dependencies'] += 1
                elif 'no module' in error:
                    skip_categories['Missing Modules'] += 1
                else:
                    skip_categories['Build/Environment'] += 1
            
            json_table_data.append([
                version,
                data['tests_run'],
                data['tests_failed'],
                data['tests_skipped'],
                f"{success_rate:.2f}%",
                skip_categories['Platform Dependencies'],
                skip_categories['Resource Dependencies'],
                skip_categories['Missing Modules'],
                skip_categories['Build/Environment']
            ])
        
        # Write JSON Results table using tabulate
        f.write("### JSON Results Summary\n")
        f.write(tabulate(json_table_data, headers=json_headers, tablefmt="pipe", numalign="right", stralign="left"))
        
        # Prepare XML Results Summary Table data
        xml_headers = ["Python Version", "Total Tests", "Errors", "Failures", "Skipped", "Success Rate"]
        xml_table_data = []
        
        for version in sorted(results_by_version.keys(), reverse=True):
            if 'xml' in results_by_version[version]:
                xml_data = results_by_version[version]['xml']
                success_rate = 100 * (xml_data['total_tests'] - xml_data['total_errors'] - xml_data['total_failures']) / xml_data['total_tests']
                
                xml_table_data.append([
                    version,
                    f"{xml_data['total_tests']:,}",
                    xml_data['total_errors'],
                    xml_data['total_failures'],
                    xml_data['skipped_tests'],
                    f"{success_rate:.2f}%"
                ])
        
        # Write XML Results table using tabulate
        f.write("\n\n### XML Results Summary\n")
        f.write(tabulate(xml_table_data, headers=xml_headers, tablefmt="pipe", numalign="right", stralign="left"))
        
        f.write("\n")
    
    return report_file

def extract_failures(xml_root):
    """Extract failure details from XML test results"""
    failures = []
    for testcase in xml_root.findall('.//testcase'):
        failure = testcase.find('failure')
        error = testcase.find('error')
        if failure is not None or error is not None:
            test_name = testcase.get('name', 'Unknown test')
            test_class = testcase.get('classname', '')
            if test_class and test_name != 'Unknown test':
                test_name = f"{test_class}.{test_name}"
            
            failure_detail = {
                'name': test_name,
                'type': 'failure' if failure is not None else 'error',
                'message': (failure.get('message') if failure is not None 
                          else error.get('message')) if failure is not None or error is not None else 'No message'
            }
            failures.append(failure_detail)
    return failures

if __name__ == "__main__":
    run_focused_comparison()
