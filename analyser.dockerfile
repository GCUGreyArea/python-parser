FROM python:latest

WORKDIR /analyser

COPY analyser/ .

RUN pip install pymongo pyyaml
ENV PATH=/analyser:$PATH

EXPOSE 27017 27017

ENTRYPOINT ["python3", "-u", "analyser.py"]
