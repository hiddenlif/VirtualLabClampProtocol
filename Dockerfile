FROM python:3.11-slim-bookworm
RUN pip install --no-cache-dir numpy==2.2.6 scipy==1.15.3
WORKDIR /app
COPY app /app
RUN chown -R 1000:1000 /app
CMD ["sleep", "infinity"]
