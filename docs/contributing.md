# Contributing

We welcome contributions to Django Easy Cache!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/django-easy-cache.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`

## Development Setup

### Using Docker (Recommended)

```bash
docker-compose up -d
docker-compose exec dev bash
```

### Local Development

We use [uv](https://docs.astral.sh/uv/) for fast Python package management. Install uv first:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

Then set up the development environment:

```bash
# Install the project with dev dependencies
uv sync --extra dev --extra redis --extra postgresql

# Run migrations
uv run python manage.py migrate
```

Alternatively, you can still use pip:

```bash
pip install -e ".[dev,redis,postgresql]"
python manage.py migrate
```

## Making Changes

1. Make your changes
2. Add tests for your changes
3. Run the test suite: `pytest`
4. Run linting: `ruff check .`
5. Run type checking: `mypy .`

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=easy_cache

# Run specific test file
uv run pytest tests/test_decorators.py

# Or without uv prefix
pytest
pytest --cov=easy_cache
```

## Code Style

We use:
- **Ruff** for linting and formatting
- **Mypy** for type checking
- **Pre-commit hooks** for automated checks

Install pre-commit hooks:

```bash
uv run pre-commit install
```

Run linting and type checking:

```bash
# Lint with ruff
uv run ruff check .

# Format with ruff
uv run ruff format .

# Type check with mypy
uv run mypy .
```

## Submitting Changes

1. Commit your changes: `git commit -m 'Add amazing feature'`
2. Push to your branch: `git push origin feature/amazing-feature`
3. Open a Pull Request

## Pull Request Guidelines

- Write clear, descriptive commit messages
- Include tests for new features
- Update documentation as needed
- Ensure all tests pass
- Follow the existing code style

## Bug Reports

Please include:
- Django version
- Python version
- Django Easy Cache version
- Minimal code to reproduce the issue
- Expected vs actual behavior

Submit bug reports at: [GitHub Issues](https://github.com/pbergen/django-easy-cache/issues)

## Feature Requests

We love feature ideas! Please submit them at: [GitHub Discussions](https://github.com/pbergen/django-easy-cache/discussions)

## Security Issues

For security vulnerabilities, please email: security@django-easy-cache.com

Do not open public issues for security vulnerabilities.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
