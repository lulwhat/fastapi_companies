###########
# BUILDER #
###########

FROM python:3.12.2-alpine AS builder

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# reqs
RUN apk update \
    && apk add postgresql-dev geos-dev gcc python3-dev musl-dev
COPY ./requirements.txt ./requirements.txt
RUN pip install --upgrade pip
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r ./requirements.txt


########
# BASE #
########

FROM python:3.12.2-alpine AS base

ENV HOME=/home/app
ENV APP_HOME=/home/app/web

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH=/home/app/web/app

# setup user app
RUN mkdir -p $APP_HOME \
    && addgroup -S app \
    && adduser -S app -G app \
    && apk update \
    && apk add libpq geos

# reqs
COPY --from=builder /usr/src/app/wheels /wheels
RUN pip install --no-cache /wheels/*
RUN pip install --no-cache-dir geoalchemy2[shapely]
COPY ./setup.py ./setup.py
RUN pip install -e .


WORKDIR $APP_HOME


###########
# BACKEND #
###########

FROM base AS backend

COPY ./alembic.ini ./entrypoint.sh ./load_initial_data.py ./pytest.ini .
COPY ./alembic ./alembic
COPY ./app ./app

RUN chown -R app:app .
RUN mkdir -p ./app/exports && chown -R app:app ./app/exports && chmod -R u+w /home/app/web
USER app

RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]


##########
# WORKER #
##########

FROM base AS worker

COPY ./app ./app
RUN chown -R app:app .
USER app

CMD ["python", "-u", "-m", "app.rabbitmq.consumer"]