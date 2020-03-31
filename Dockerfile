FROM python:3.6.10-alpine3.10
MAINTAINER Pierre-Francois Duc <pierre-francois.duc@rl-institut.de>

ARG branch=dev
ARG POSTGRES_url
ARG POSTGRES_user
ARG POSTGRES_pw
ARG POSTGRES_db

ENV POSTGRES_URL=$POSTGRES_url
ENV POSTGRES_USER=$POSTGRES_user
ENV POSTGRES_PW=$POSTGRES_pw
ENV POSTGRES_DB=$POSTGRES_db

COPY docker_postgres_login_help.py /
COPY app /app
COPY index.py /

# options for gunicorn
ENV GUNICORN_CMD_ARGS=--bind=0.0.0.0:5000 --workers=2

RUN apk update
RUN apk add --virtual build-deps gcc musl-dev postgresql-dev git

# this helps using the cache of docker
COPY app/requirements.txt /
RUN pip install -r /requirements.txt
RUN pip install gunicorn
RUN git clone --single-branch --branch $branch https://github.com/rl-institut/NESP2.git

# Setup flask application
RUN mkdir -p /src


RUN python /app/setup_maps.py -docker

#WORKDIR /app

EXPOSE 5000

RUN python /docker_postgres_login_help.py

# Start gunicorn
CMD ["gunicorn", "index:app"]