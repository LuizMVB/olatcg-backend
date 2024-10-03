# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9-slim-buster

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
COPY setup.sh .
COPY ./build /build
COPY ./app /app

WORKDIR /app

RUN chmod +x /setup.sh && /setup.sh

ENV PATH="/scripts:/py/bin:$PATH"
ENV BLASTDB="/blast/db"

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app.wsgi"]
