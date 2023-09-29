FROM python:latest

WORKDIR /parser

COPY parser/ .

RUN pip install pyyaml flask pymongo
ENV PATH=/parser:$PATH

EXPOSE 5000 5000

ENTRYPOINT ["python3", "-u", "server.py"]
