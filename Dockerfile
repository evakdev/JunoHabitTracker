FROM python:3.9
WORKDIR /app
COPY . .
RUN apk update
RUN apk add gcc
RUN apk add linux-headers
RUN apk add musl-dev
RUN pip install -r ./requirements.txt --use-deprecated=backtrack-on-build-failures
CMD [ "python", "./project/run.py" ]