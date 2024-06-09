FROM --platform=linux/amd64 alpine:latest

RUN apk update && \
    apk upgrade --no-cache && \
    apk add python3 py3-flask --no-cache

COPY hello_evolve.py /

EXPOSE 5000/tcp

ENTRYPOINT ["python", "/hello_evolve.py"]
