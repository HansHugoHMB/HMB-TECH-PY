FROM python:3.11-slim

RUN pip install proxy.py

EXPOSE 8080

CMD ["proxy", "run", "--port", "8080"]