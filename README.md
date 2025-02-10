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
uv venv -p python3.9 venv; source venv/bin/activate; uv pip install -r requirements.txt 
source venv/bin/acticate
``

Then run a quick acceptance test, and benchmark python versions.
```

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
