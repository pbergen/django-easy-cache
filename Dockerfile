# source and inspiration: https://github.com/nklsw/django-docker-starter/blob/main/Dockerfile

# Set Python version
ARG PYTHON_MINOR_VERSION=3.11

### STAGE 1: Build python ###
FROM ghcr.io/astral-sh/uv:python${PYTHON_MINOR_VERSION}-trixie-slim AS builder

# Build arguments for controlling optional dependencies
ARG UV_INSTALL_DEV=false
ARG UV_INSTALL_REDIS=false
ARG UV_INSTALL_POSTGRESQL=false
ARG UV_INSTALL_PUBLISHING=false
ARG UV_INSTALL_DOCS=false
ARG UV_INSTALL_ALL=false

# Set work directory
WORKDIR /app

ARG UID=1000
ARG GID=1000

RUN groupadd -g "${GID}" app \
  && useradd --create-home --no-log-init -u "${UID}" -g "${GID}" app \
  && mkdir -p /app/staticfiles \
  && mkdir -p /.venv \
  && chown app:app -R /app/staticfiles /app /.venv

USER app

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Copy project configuration files first (for better Docker layer caching)
COPY --chown=app:app uv.lock pyproject.toml ./

# Copy source code for the django_easy_cache package
COPY --chown=app:app easy_cache/ ./easy_cache/

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/home/app/.cache/uv,uid=1000,gid=1000 \
    EXTRAS=""; \
    if [ "$UV_INSTALL_DEV" = "true" ] || [ "$UV_INSTALL_DEV" = "1" ]; then \
        EXTRAS="$EXTRAS dev"; \
    fi; \
    if [ "$UV_INSTALL_REDIS" = "true" ] || [ "$UV_INSTALL_REDIS" = "1" ]; then \
        EXTRAS="$EXTRAS redis"; \
    fi; \
    if [ "$UV_INSTALL_POSTGRESQL" = "true" ] || [ "$UV_INSTALL_POSTGRESQL" = "1" ]; then \
        EXTRAS="$EXTRAS postgresql"; \
    fi; \
    if [ "$UV_INSTALL_PUBLISHING" = "true" ] || [ "$UV_INSTALL_PUBLISHING" = "1" ]; then \
        EXTRAS="$EXTRAS publishing"; \
    fi; \
    if [ "$UV_INSTALL_DOCS" = "true" ] || [ "$UV_INSTALL_DOCS" = "1" ]; then \
        EXTRAS="$EXTRAS docs"; \
    fi; \
    if [ -n "$EXTRAS" ]; then \
        uv sync --frozen $(echo "$EXTRAS" | sed 's/^ *//' | sed 's/ *$//' | sed 's/ / --extra /g' | sed 's/^/--extra /'); \
    else \
        uv sync --frozen --no-dev; \
    fi

# Copy the rest of the application files
COPY --chown=app:app . ./


### STAGE 2: Setup ###
FROM ghcr.io/astral-sh/uv:python${PYTHON_MINOR_VERSION}-trixie-slim

# Install required OS dependencies
# We have to have "gettext" here as well to be able to run "makemigrations"
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
      # Translations dependencies:
      gettext \
      git \
      locales \
      make && \
    sed -i -e "s/# en_GB.UTF-8.*/en_GB.UTF-8 UTF-8/" /etc/locale.gen && \
    sed -i -e "s/# de_DE.UTF-8.*/de_DE.UTF-8 UTF-8/" /etc/locale.gen && \
    locale-gen de_DE.UTF-8 &&\
    update-locale LANG=de_DE.UTF-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Directory in container for project source files
ENV PROJECT_HOME=/app

# Declare locales
ENV LANG=de_DE.UTF-8
ENV LANGUAGE=de_DE:de
ENV LC_ALL=de_DE.UTF-8
ENV PYTHONUNBUFFERED=1

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:/.venv/bin:$PATH" \
    USER="app"

# Create application subdirectories
WORKDIR $PROJECT_HOME

ARG UID=1000
ARG GID=1000

RUN groupadd -g "${GID}" app \
  && useradd --create-home --no-log-init -u "${UID}" -g "${GID}" app

# Copy application source code to project home
COPY --from=builder --chown=app:app /app $PROJECT_HOME
COPY --from=builder --chown=app:app /.venv/ /.venv

# EXPOSE port 8000 to allow communication to/from server
EXPOSE 8000

CMD ["bash"]
