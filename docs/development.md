# Development

## Docker Development

### Quick Start with Docker

Start the development environment:

```bash
docker-compose up -d
```

This will start:
- Django application with auto-reload
- Redis cache backend
- PostgreSQL database
- Qdrant vector database

### Docker Build Options

You can control which optional dependencies are installed during the Docker build process using build arguments:

```bash
# Build with all dependencies (default in docker-compose.yml)
docker-compose build

# Build with only core dependencies
docker build --build-arg UV_INSTALL_DEV=false --build-arg UV_INSTALL_REDIS=false --build-arg UV_INSTALL_POSTGRESQL=false -t django-easy-cache .

# Build with development dependencies only
docker build --build-arg UV_INSTALL_DEV=true --build-arg UV_INSTALL_REDIS=false --build-arg UV_INSTALL_POSTGRESQL=false -t django-easy-cache .

# Build with Redis support only
docker build --build-arg UV_INSTALL_DEV=false --build-arg UV_INSTALL_REDIS=true --build-arg UV_INSTALL_POSTGRESQL=false -t django-easy-cache .

# Build with PostgreSQL support only
docker build --build-arg UV_INSTALL_DEV=false --build-arg UV_INSTALL_REDIS=false --build-arg UV_INSTALL_POSTGRESQL=true -t django-easy-cache .

# Custom docker-compose override
```

Example docker-compose.override.yml:

```yaml
services:
  dev:
    build:
      args:
        UV_INSTALL_DEV: "true"
        UV_INSTALL_REDIS: "true"
        UV_INSTALL_POSTGRESQL: "false"
```

### Available Build Arguments

- `UV_INSTALL_DEV`: Install development dependencies (default: true)
- `UV_INSTALL_REDIS`: Install Redis dependencies (default: true)
- `UV_INSTALL_POSTGRESQL`: Install PostgreSQL dependencies (default: true)
- `UV_INSTALL_DOCS`: Install documentation dependencies (default: true)

These can be combined as needed. For example, you can install both dev and Redis dependencies by setting both flags to "true".

## Testing Support

Easy Cache includes comprehensive testing utilities.

### Running Tests

Using uv (recommended):

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=easy_cache

# Run specific test file
uv run pytest tests/test_decorators.py
```

Using Docker:

```bash
docker-compose exec dev pytest
```

Using pip/virtualenv:

```bash
pytest
pytest --cov=easy_cache
```

### Test Coverage

The project maintains high test coverage (86%+) with tests for:

- Time-based and cron-based decorators
- Object parameter caching and serialization
- Cache key generation and validation
- Analytics tracking
- Edge cases and error handling
- Django model integration
- Management commands

## Building Documentation

### Local Build

```bash
cd docs
make html
```

The HTML documentation will be in `docs/_build/html/`.

### Docker Build

```bash
docker-compose exec dev bash -c "cd docs && make html"
```

### Documentation Structure

- `docs/getting-started.md` - Installation and quick start
- `docs/features/` - Feature documentation
- `docs/api-reference.md` - API reference
- `docs/development.md` - Development guide
- `docs/contributing.md` - Contribution guidelines
