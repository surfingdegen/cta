# Contributing to Crypto Trading Agent

Thank you for your interest in contributing to the Crypto Trading Agent project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

- A clear, descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Any relevant logs or error messages
- Your environment (OS, Python version, etc.)

### Suggesting Enhancements

We welcome suggestions for enhancements! Please create an issue with:

- A clear, descriptive title
- A detailed description of the enhancement
- Any relevant examples or use cases
- If applicable, any references or resources

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Add or update tests as necessary
5. Ensure all tests pass
6. Update documentation as needed
7. Submit a pull request

#### Pull Request Guidelines

- Follow the existing code style
- Include tests for new features or bug fixes
- Update documentation for any changed functionality
- Keep pull requests focused on a single change
- Link to any relevant issues

## Development Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/crypto-trading-agent.git
   cd crypto-trading-agent
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```
   pip install -e .
   ```

5. Run tests:
   ```
   python test_agent.py
   ```

## Project Structure

- `src/`: Source code
  - `wallet.py`: Blockchain wallet management
  - `technical_analysis.py`: Technical analysis module
  - `sentiment_analysis.py`: Sentiment analysis module
  - `trading_strategy.py`: Trading strategy implementation
  - `main.py`: Main entry point
- `config/`: Configuration files
- `logs/`: Log files
- `test_agent.py`: Test script

## Coding Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all functions, classes, and modules
- Keep functions focused on a single responsibility
- Use meaningful variable and function names

## Testing

- Write tests for new features
- Ensure all tests pass before submitting a pull request
- Consider edge cases in your tests

## Documentation

- Update the README.md file with any new features or changes
- Document any new configuration options
- Add docstrings to new functions and classes

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.
