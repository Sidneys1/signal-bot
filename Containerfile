# syntax=docker/dockerfile:experimental
FROM scratch AS source
COPY pyproject.toml src /

FROM python:3.12-alpine
RUN --mount=type=bind,from=source,target=/signal_bot_framework,source=/,rw --mount=type=cache,target=/cache --mount=type=tmpfs,target=/temp \
  TMPDIR=/temp python -m pip install --cache-dir=/cache /signal_bot_framework
