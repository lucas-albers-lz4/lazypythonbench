# Contributing to Lazypythonbench

Thanks for your interest in contributing! This project is a benchmarking tool for comparing Python version performance, and contributions of all kinds are welcome.

## How to contribute

### Reporting issues

- Open a [GitHub issue](https://github.com/lucas-albers-lz4/lazypythonbench/issues) with a clear description of the problem
- Include the Python versions tested, OS, and relevant error output

### Submitting changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Make your changes
4. Run the benchmark and test suite to verify nothing is broken:
   ```bash
   ./benchmark.py --disable-benchmark --disable-system-check
   ```
5. Commit with a clear message describing the change
6. Push and open a pull request

### Development setup

The project uses:
- **black** for code formatting
- **flake8** for linting
- **pytest** for test discovery

Run lint and tests before submitting:

```bash
black benchmark.py
flake8 benchmark.py
pytest
```

## Code of conduct

Please be respectful and constructive in all project interactions.
