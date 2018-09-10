FROM python:alpine
RUN apk add --no-cache jq git
RUN mkdir -p /code
COPY . /usr/src/app
WORKDIR /usr/src/app
RUN easy_install /usr/src/app
WORKDIR /code
ENTRYPOINT [ "/usr/src/app/run-scan.sh" ]
