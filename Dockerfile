FROM python:3.13-slim-bookworm

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Python environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# Working directory
WORKDIR /app

# Copy project configuration first (for better caching)
COPY pyproject.toml ./
COPY MANIFEST.in ./

# Install dependencies using uv (this layer will be cached)
RUN uv sync --dev

# Copy source code
COPY django_smart_cache/ ./django-smart-cache/

# Install package in development mode
RUN uv pip install -e .

# Copy any additional files needed for testing
COPY . .

# Create test project structure and set permissions
RUN mkdir -p test_project logs && \
    chmod -R 755 /app

# Default command for interactive development
CMD ["bash"]
