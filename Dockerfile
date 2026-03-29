FROM python:3.9-slim

# Install 1Password CLI
ARG OP_VERSION=2.29.0
RUN apt-get update && apt-get install -y --no-install-recommends unzip curl && \
    curl -sSfo op.zip "https://cache.agilebits.com/dist/1P/op2/pkg/v${OP_VERSION}/op_linux_amd64_v${OP_VERSION}.zip" && \
    unzip -o op.zip op -d /usr/local/bin/ && \
    rm op.zip && \
    apt-get purge -y unzip curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn run:app --bind 0.0.0.0:${PORT:-8000} --workers 2
