FROM namlehong/alpine-pgo-base:latest

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENTRYPOINT ["/usr/bin/python", "pokecli.py"]
