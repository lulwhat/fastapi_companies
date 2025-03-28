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
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


#########
# FINAL #
#########

FROM python:3.12.2-alpine

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
COPY . .

RUN chown -R app:app .
USER app

RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]