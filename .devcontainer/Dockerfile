FROM mcr.microsoft.com/devcontainers/python:3.13

ENV DEBIAN_FRONTEND=noninteractive

# Install Docker CLI and buildx plugin
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Install Docker buildx plugin
RUN mkdir -p /usr/local/lib/docker/cli-plugins \
    && curl -fsSL "https://github.com/docker/buildx/releases/download/v0.19.3/buildx-v0.19.3.linux-$(dpkg --print-architecture)" \
       -o /usr/local/lib/docker/cli-plugins/docker-buildx \
    && chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx

# Add vscode user to docker group for socket access
RUN groupadd -f docker && usermod -aG docker vscode

WORKDIR /workspaces/weightmelters

# Use project venv when present
ENV PATH="/workspaces/weightmelters/.venv/bin:${PATH}"

# Auto-activate venv in interactive shells
RUN echo 'if [ -f /workspaces/weightmelters/.venv/bin/activate ]; then . /workspaces/weightmelters/.venv/bin/activate; fi' >> /root/.bashrc
