FROM apache/spark:4.2.0-python3

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

USER root
WORKDIR /app

COPY . /app/

RUN apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y --no-install-recommends python3.14 python3.14-dev python3.14-venv && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.14 1 && \
    update-alternatives --set python3 /usr/bin/python3.14 && \
    rm -rf /var/lib/apt/lists/* && \
    uv pip install --system --no-cache .[spark]

USER spark
