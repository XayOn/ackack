FROM python:3.10-bullseye as build

RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime

WORKDIR /app
ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    VENV_PATH=/app/.venv \
    PATH="/root/.local/bin:$VENV_PATH/bin:$PATH"

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root --no-interaction --no-ansi

FROM python:3.10-bullseye as runtime
WORKDIR /app

COPY --from=build /root/.local/share/pypoetry /root/.local/share/pypoetry 
COPY --from=build /root/.local/bin/poetry /root/.local/bin/poetry
COPY --from=build $VENV_PATH $VENV_PATH

ENV PATH="/root/.local/bin:$VENV_PATH/bin:$PATH"
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock /app/

RUN poetry install --no-dev --no-root
COPY . ./
RUN poetry install --no-dev

RUN echo "deb https://www.deb-multimedia.org stable main non-free" > /etc/apt/sources.list.d/dmo.list 
RUN apt-get update -oAcquire::AllowInsecureRepositories=true \
    && apt-get install -y --allow-unauthenticated ffmpeg \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8000
CMD "/app/docker-entrypoint.sh"
