FROM python:3
ADD project/
ADD .gitignore
ADD LICENCE
ADD README.md
ADD requirements.txt
RUN pip install -r ./requirements.txt/
CMD [ "python", "./project/run.py" ]