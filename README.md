# Python Version Performance Comparison Tool

A tool for benchmarking and comparing different Python versions' performance and test results.

## Features

- Automated performance benchmarking across multiple Python versions
- Comprehensive test suite comparison
- System environment validation
- Detailed markdown report generation
- Support for quick vs full benchmark modes

## Prerequisites

- macOS (currently optimized for macOS, contributions welcome for other platforms)
- Python 3.9 or higher
- Homebrew (for managing Python versions)

## Installation

1. Clone the repository:

2. Create the virtual envi
I like how fast uv is at creating virtual enviroments.
On macos it's a copy on write creation, so fast and space optimal.

```
uv venv -p python3.12 venv; source venv/bin/activate; uv pip install -r requirements.txt 
Using CPython 3.12.9 interpreter at: /opt/homebrew/opt/python@3.12/bin/python3.12
Creating virtual environment at: venv
Activate with: source venv/bin/activate
Using Python 3.12.9 environment at: venv
Resolved 17 packages in 271ms
Prepared 9 packages in 559ms
Installed 17 packages in 15ms
 + black==25.1.0
 + click==8.1.8
 + flake8==7.1.1
 + iniconfig==2.0.0
 + mccabe==0.7.0
 + mypy-extensions==1.0.0
 + packaging==24.2
 + pathspec==0.12.1
 + platformdirs==4.3.6
 + pluggy==1.5.0
 + psutil==6.1.1
 + pycodestyle==2.12.1
 + pyflakes==3.2.0
 + pyperf==2.8.1
 + pyperformance==1.11.0
 + pytest==8.3.4
 + tabulate==0.9.0
```

## Output

Results are saved in:
- `benchmark_results/`: Performance benchmark results
- `test_results/`: Test suite results
- Comparison reports are generated as markdown files

## 🔍 System Requirements

The tool performs several system checks before running benchmarks:
- Power source (AC power required)
- Available memory (minimum 25% of total RAM)
- Background processes (Spotlight indexing, Time Machine)
- System load and CPU usage

## 📚 Documentation

For detailed information about:
- Benchmark methodology
- System requirements
- Test suite details
- Report interpretation

See the [docs](docs/README.md) directory.

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
