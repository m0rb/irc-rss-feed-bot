FROM python:3.8-slim-buster as build
WORKDIR /app
RUN sed -i 's/@SECLEVEL=2/@SECLEVEL=1/' /etc/ssl/openssl.cnf && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r ./requirements.txt
# Note: Regarding SECLEVEL, see https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=927461
# Lowering the SECLEVEL causes more https certificates to be valid.
COPY ircrssfeedbot ircrssfeedbot
RUN groupadd -g 999 app && \
    useradd -r -m -u 999 -g app app
USER app
ENTRYPOINT ["python", "-m", "ircrssfeedbot"]
CMD ["--config-path", "/config/config.yaml"]
STOPSIGNAL SIGINT

FROM build as test
WORKDIR /app
USER root
COPY pylintrc pyproject.toml requirements-dev.in setup.cfg ./
COPY scripts/test.sh ./scripts/test.sh
RUN pip install --no-cache-dir -Ur requirements-dev.in && \
    ./scripts/test.sh

FROM build
