# BornAgain Bot Test Suite

Comprehensive unit and integration tests for the BornAgain Discord bot.

## Setup

```bash
pip install -r tests/requirements-test.txt
```

## Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Unit tests only
pytest -m "not integration"

# Specific file
pytest tests/unit/util/test_input_validation_utils.py -v
```
