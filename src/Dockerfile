FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

WORKDIR /app/

ENV TZ="Asia/Tehran"

# Install Poetry
RUN python3 -m pip install poetry
RUN POETRY_HOME=/opt/poetry python

# Install system dependencies
RUN apt-get update && apt-get install -y minify dos2unix

# Install Poetry
RUN python3 -m pip install poetry

COPY ./pyproject.toml ./poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"

ENV PYTHONPATH=/app

COPY . /app

# Make start script executable
RUN chmod +x start.sh && dos2unix start.sh

# Minify static files for production
RUN bash -c "if [[ -z '$DEBUG' ]]; then minify -a -r css/ -o ./ && minify -a -r js/ -o ./; fi"
