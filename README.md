# Python Version Performance Comparison Tool

A tool for benchmarking and comparing different Python versions' performance and test results.

## Features

- Automated performance benchmarking across multiple Python versions
- Comprehensive test suite comparison
- System environment validation
- Detailed markdown report generation
- Support for quick vs full benchmark modes

## Prerequisites

- macOS or Linux
- Python 3.9 or higher
- Homebrew (for managing Python versions)

## Installation

1. Clone the repository:

2. Create the virtual environment and install the dependencies.

Example using uv
```
uv venv -p python3.9 venv; source venv/bin/activate; uv pip install -r requirements.txt 
source venv/bin/activate
```

Then run a quick acceptance test, and benchmark python versions.
```
./benchmark.py --disable-benchmark --disable-system-check
```

Then run the full benchmark.
```
./benchmark.py
```

The benchmark will take hours to complete.

## Output

Results are saved in:
- `benchmark_results/`: Performance benchmark results
- `test_results/`: Test suite results
- Comparison reports are generated as markdown files

## 🔍 System Requirements

The tool performs several system checks before running benchmarks: (MacOS only)
- Power source (AC power required)
- Available memory (minimum 25% of total RAM)
- Background processes (Spotlight indexing, Time Machine)
- System load and CPU usage

See example results in [docs/example_results.md](docs/example_results.md) 
explanation of the test results in [docs/comparison_approach.md](docs/comparison_approach.md) 
example benchmark report in [docs/benchmark_comparison.md](docs/benchmark_comparison.md)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
