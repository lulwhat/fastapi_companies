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
COPY ./setup.py .
COPY ./app ./app
RUN pip install --upgrade pip
RUN pip install -e .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r ./app/requirements.txt


########
# BASE #
########

FROM python:3.12.2-alpine AS base

ENV HOME=/home/app
ENV APP_HOME=/home/app/web

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

WORKDIR $APP_HOME

# copy project
COPY ./app ./app

RUN chown -R app:app .
RUN mkdir -p ./app/exports && chown -R app:app ./app/exports && chmod -R 777 ./app/exports
USER app


#######
# APP #
#######

FROM base AS app

RUN chmod +x ./app/entrypoint.sh
ENTRYPOINT ["./app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "./app"]


##########
# WORKER #
##########

FROM base AS worker

CMD ["python", "-u", "-m", "app.rabbitmq.consumer"]