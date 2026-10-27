# Stage 1: Install Python dependencies. The runtime image has no pip or shell.
FROM registry.access.redhat.com/hi/python:3.14-builder AS build-image
ARG http_proxy
ARG https_proxy
ARG no_proxy

ENV http_proxy=$http_proxy \
    https_proxy=$https_proxy \
    no_proxy=$no_proxy \
    HTTP_PROXY=$http_proxy \
    HTTPS_PROXY=$https_proxy \
    NO_PROXY=$no_proxy

USER root
WORKDIR /app

COPY requirements.txt .
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# CVE-2026-24049
RUN pip install --no-cache-dir --upgrade "wheel>=0.46.2" && \
    pip install --no-cache-dir -r requirements.txt && \
    chmod -R a+rX /opt/venv

# Stage 2: Red Hat Hardened Python. No shell; healthcheck uses the stdlib client.
FROM registry.access.redhat.com/hi/python:3.14 AS runtime-image
ARG http_proxy
ARG https_proxy
ARG no_proxy

ENV http_proxy=$http_proxy \
    https_proxy=$https_proxy \
    no_proxy=$no_proxy \
    HTTP_PROXY=$http_proxy \
    HTTPS_PROXY=$https_proxy \
    NO_PROXY=$no_proxy \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=build-image /opt/venv /opt/venv
COPY ./app/ ./app/

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD ["python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')"]

# Image default command is python3, which does not see the venv packages.
ENTRYPOINT ["/opt/venv/bin/python3"]
CMD ["-m", "uvicorn", "app.main:app", "--host", "", "--port", "8000"]
