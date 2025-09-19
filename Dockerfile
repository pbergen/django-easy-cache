# source and inspiration: https://github.com/nklsw/django-docker-starter/blob/main/Dockerfile

# Set Python version
ARG PYTHON_MINOR_VERSION=3.11

### STAGE 1: Build python ###
FROM ghcr.io/astral-sh/uv:python${PYTHON_MINOR_VERSION}-bookworm-slim AS builder

# Build argument to control dev dependencies
ARG UV_INSTALL_DEV=false

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

# Copy source code for the django_smart_cache package
COPY --chown=app:app django_smart_cache/ ./django_smart_cache/

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/home/app/.cache/uv,uid=1000,gid=1000 \
    if [ "$UV_INSTALL_DEV" = "false" ] || [ "$UV_INSTALL_DEV" = "0" ]; then \
        uv sync --frozen  --no-dev; \
    else \
        uv sync --frozen  --extra dev; \
    fi

# Copy the rest of the application files
COPY --chown=app:app . ./


### STAGE 2: Setup ###
FROM ghcr.io/astral-sh/uv:python${PYTHON_MINOR_VERSION}-bookworm-slim

# Install required OS dependencies
# We have to have "gettext" here as well to be able to run "makemigrations"
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
      # Translations dependencies:
      gettext \
      git \
      locales && \
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
