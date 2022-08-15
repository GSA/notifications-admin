FROM mcr.microsoft.com/vscode/devcontainers/python:0-3.9

# RUN groupadd --gid 1000 node \
#     && useradd --uid 1000 --gid node --shell /bin/bash --create-home node

ENV NODE_VERSION 16.15.1

RUN apt-get update \
    && apt-get -y install --no-install-recommends apt-utils 2>&1 \
    && apt-get -y install \
    curl \
    emacs \
    exa \
    fd-find \
    git \
    iproute2 \
    less \
    libsodium-dev \
    lsb-release \
    man-db \
    manpages \
    net-tools \
    openssh-client \
    procps \
    sudo \
    tldr \
    unzip \
    vim \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

RUN groupadd --gid 1001 node \
    && useradd --uid 1001 --gid node --shell /bin/bash --create-home node

COPY package-lock.json ./
COPY package.json ./
COPY devcontainer-admin/scripts/notify-admin-entrypoint.sh ./

ENV SHELL /bin/zsh

EXPOSE 6012
