FROM python:3.9-alpine
WORKDIR /app
COPY . .
RUN pip install -r ./requirements.txt --use-deprecated=backtrack-on-build-failures
CMD [ "python", "./project/run.py" ]