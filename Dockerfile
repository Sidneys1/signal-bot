# syntax=docker/dockerfile:experimental
FROM python:3.11-alpine
RUN --mount=type=bind,target=/signal_bot,source=/,rw --mount=type=cache,target=/cache --mount=type=tmpfs,target=/temp \
  TMPDIR=/temp python -m pip install --cache-dir=/cache /signal_bot
