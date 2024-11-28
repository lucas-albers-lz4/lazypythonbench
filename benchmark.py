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

# Constants
BREWPATH = "/opt/homebrew/bin/"
PYTHON_BASE_VERSIONS = [
    "3.9",
    "3.12",
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

def run_benchmark(python_path, output_dir, quick_mode=False):
    """Run benchmarks for testing report generation
    
    Args:
        python_path (str): Path to Python executable
        output_dir (Path/str): Directory to store benchmark results
        quick_mode (bool): If True, runs only pyflate benchmark
        
    Returns:
        Path/None: Path to benchmark results file if successful, None if failed
        
    Notes:
        - Checks system settings before running benchmarks
        - Creates timestamped JSON file for results
        - Runs all benchmarks (json_dumps,richards,pyflate) if quick_mode is False
        - Runs only pyflate benchmark if quick_mode is True
        - Uses quiet environment settings to reduce output noise
    """
    # First check system settings
    print("\nChecking system settings for benchmark suitability...")
    is_suitable, issues = check_system_settings()
    
    if not is_suitable:
        print("\n⚠️  Warning: System settings may affect benchmark accuracy:")
        for issue in issues:
            print(f"  • {issue}")
        
        response = input("\nContinue with benchmarks anyway? (y/N): ").lower()
        if response != 'y':
            print("Benchmarks aborted.")
            return None
    
    print("✓ System settings suitable for benchmarking")
    
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
    
    # Set benchmarks based on mode
    benchmarks = "pyflate" if quick_mode else "json_dumps,richards,pyflate"
    
    cmd = [
        python_path, "-m", "pyperformance", "run",
        "--python", python_path,
        "--benchmarks", benchmarks,
        "--output", str(output_file),
        "--inherit-environ", ",".join(QUIET_ENV.keys())
    ]
    
    try:
        print(f"\nRunning {'quick' if quick_mode else 'standard'} benchmarks with {python_path}...")
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
    headers = ["Python Version", "Tests Run", "Passed", "Failed", "Skipped"]
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
    parser.add_argument('--quick', action='store_true',
                      help='Run minimal set of tests and benchmarks')
    return parser.parse_args()

def run_focused_comparison():
    """Run both test suite and performance comparisons for multiple Python versions
    
    This function coordinates the execution of tests and benchmarks across different
    Python versions. It handles:
        - Command line argument parsing
        - System suitability checks for benchmarking
        - Virtual environment creation and management
        - Test execution (full or quick mode)
        - Benchmark execution (full or quick mode)
        - Result collection and report generation
    
    Command line options:
        --disable-test: Skip unit tests and test comparison
        --disable-benchmark: Skip performance benchmarks
        --disable-system-check: Skip system suitability check
        --quick: Run minimal set of tests and benchmarks
    """
    args = parse_arguments()
    output_dir = Path("comparison_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
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
        
        # Run tests if enabled
        if not args.disable_test:
            test_result = run_tests(venv_python, output_dir, quick_mode=args.quick)
            if test_result:
                test_results.append(test_result)
        
        # Run benchmarks if enabled
        if not args.disable_benchmark:
            perf_result = run_benchmark(venv_python, output_dir, quick_mode=args.quick)
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
        
        # Keep existing comparison functionality
        for i in range(len(perf_results)-1):
            print(f"\nComparing {Path(perf_results[i]).name} vs {Path(perf_results[i+1]).name}:")
            subprocess.run([
                comparison_python,
                "-m", "pyperf", "compare_to",
                "--table", str(perf_results[i]), str(perf_results[i+1])
            ], check=True)
        
        # Add markdown report generation
        report_file = output_dir / f"benchmark_comparison_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"
        with open(report_file, 'w') as f:
            f.write("# Python Performance Comparison\n\n```\n")
            subprocess.run([
                comparison_python, "-m", "pyperf", "compare_to",
                "--table", *[str(result) for result in perf_results]
            ], stdout=f, check=True)
            f.write("```\n")
        print(f"\nMarkdown comparison report generated: {report_file}")

    print("\nComparison complete. Results are in the 'comparison_results' directory.")

if __name__ == "__main__":
    run_focused_comparison()