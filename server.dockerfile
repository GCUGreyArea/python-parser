FROM python:latest

WORKDIR /parser

COPY . .

RUN pip install --upgrade pip
RUN pip install pyyaml flask
ENV PATH=/parser:$PATH

EXPOSE 5000 5000

ENTRYPOINT ["python3", "server.py"]
