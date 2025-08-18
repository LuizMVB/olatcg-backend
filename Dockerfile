FROM python:3.9-slim-bookworm

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
COPY setup.sh .
COPY ./build /build
COPY ./app /app
COPY ./blast /blast

WORKDIR /app

RUN chmod +x /setup.sh && /setup.sh

ENV PATH="/scripts:/py/bin:$PATH"
ENV BLASTDB="/blast/db"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app.wsgi"]