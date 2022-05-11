FROM python:3.9
WORKDIR /app
COPY . .
RUN apt-get update
RUN pip install -r ./requirements.txt --use-deprecated=backtrack-on-build-failures
CMD [ "python", "./project/run.py" ]