FROM python:3.9-alpine
WORKDIR /app
COPY . .
RUN apk update
RUN apk add gcc
RUN apk add linux-headers
RUN apk musl-dev
RUN pip install -r ./requirements.txt --use-deprecated=backtrack-on-build-failures
CMD [ "python", "./project/run.py" ]