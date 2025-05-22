# Multi-stage build for notifications-admin
FROM node:22-slim as node-builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install Node.js dependencies
RUN npm ci --no-audit

# Copy source files needed for build
COPY app/assets ./app/assets
COPY gulpfile.js ./
COPY babel.config.js ./

# Build frontend assets
RUN npm run build

# Python builder stage
FROM python:3.12-slim as python-builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Install pip and wheel
RUN pip install --upgrade pip wheel setuptools

# Install Poetry using the official installer
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Set git commit info for version.py - use a more explicit approach
ARG GIT_COMMIT=local
RUN echo "__git_commit__ = \"${GIT_COMMIT}\"" > app/version.py && \
    echo "__time__ = \"$(date +%Y-%m-%d:%H:%M:%S)\"" >> app/version.py

# Install dependencies (no dev dependencies for smaller image)
RUN poetry install --only main --no-interaction

# Final stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from python builder stage
COPY --from=python-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy Node.js build artifacts
COPY --from=node-builder /app/app/static /app/app/static

# Copy application code
COPY . .

# Copy generated version.py from builder
COPY --from=python-builder /app/app/version.py /app/app/version.py

# Set environment variables
ENV FLASK_APP=application.py

# Login.gov sandbox settings
ENV LOGIN_DOT_GOV_CLIENT_ID="urn:gov:gsa:openidconnect.profiles:sp:sso:gsa:test_notify_gov"
ENV LOGIN_DOT_GOV_USER_INFO_URL="https://idp.int.identitysandbox.gov/api/openid_connect/userinfo"
ENV LOGIN_DOT_GOV_ACCESS_TOKEN_URL="https://idp.int.identitysandbox.gov/api/openid_connect/token"
ENV LOGIN_DOT_GOV_LOGOUT_URL="https://idp.int.identitysandbox.gov/openid_connect/logout?client_id=urn:gov:gsa:openidconnect.profiles:sp:sso:gsa:test_notify_gov&post_logout_redirect_uri=http://localhost:6012/sign-out"
ENV LOGIN_DOT_GOV_BASE_LOGOUT_URL="https://idp.int.identitysandbox.gov/openid_connect/logout?"
ENV LOGIN_DOT_GOV_SIGNOUT_REDIRECT="http://localhost:6012/sign-out"
ENV LOGIN_DOT_GOV_INITIAL_SIGNIN_URL="https://idp.int.identitysandbox.gov/openid_connect/authorize?acr_values=http%3A%2F%2Fidmanagement.gov%2Fns%2Fassurance%2Fial%2F1&client_id=urn:gov:gsa:openidconnect.profiles:sp:sso:gsa:test_notify_gov&nonce=NONCE&prompt=select_account&redirect_uri=http://localhost:6012/sign-in&response_type=code&scope=openid+email&state=STATE"
ENV LOGIN_DOT_GOV_CERTS_URL="https://idp.int.identitysandbox.gov/api/openid_connect/certs"

# Create a simple startup script
RUN echo '#!/bin/bash\n\
echo "Starting Admin UI..."\n\
exec "$@"\n' > /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

# Expose the port the app runs on
EXPOSE 6012

# Add healthcheck
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:6012/ || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Use run-flask-bare from Makefile (directly without make since we're not in a virtual env)
CMD ["flask", "run", "-p", "6012", "--host=0.0.0.0"]