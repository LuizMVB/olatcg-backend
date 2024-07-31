FROM python:3.9-slim-buster
LABEL maintainer="londonappdeveloper.com"

ENV PYTHONUNBUFFERED 1

COPY ./production.requirements.txt /requirements.txt
COPY ./app /app
COPY ./scripts /scripts
COPY ./setup.sh /setup.sh
COPY ./build /build

WORKDIR /app
RUN chmod +x /setup.sh && /setup.sh

ENV PATH="/scripts:/py/bin:$PATH"
ENV BLASTDB="/blast/db"

EXPOSE 8000

CMD ["sh", "-c", "python manage.py wait_for_db && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
