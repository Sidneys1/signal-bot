FROM python:3.11-alpine as BUILD

COPY . .

RUN python -m pip install build \
 && python -m build

FROM python:3.11-alpine

COPY --from=BUILD ./dist/*.whl /tmp/

RUN python -m pip install --no-cache-dir /tmp/*.whl \
 && rm /tmp/*.whl

