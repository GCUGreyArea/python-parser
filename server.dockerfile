FROM python:latest

WORKDIR /parser

COPY . .

RUN python3 -m venv venv
RUN . venv/bin/activate 
RUN pip install pyyaml flask
ENV PATH=/parser:$PATH

EXPOSE 5000 5000

ENTRYPOINT ["python3", "server.py"]
