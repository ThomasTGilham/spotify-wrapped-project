# Use a specific Python version as the base
FROM python:3.8-slim-buster

# Set the Airflow home directory
ENV AIRFLOW_HOME=/opt/airflow

# Install system-level dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libssl-dev \
        libffi-dev \
        libpq-dev \
        git \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Airflow version as a build argument
ARG AIRFLOW_VERSION=2.5.1

# Upgrade pip and copy requirements
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt /

# Install Airflow with postgres and www extras using a constraint file for stability
RUN pip install \
    --no-cache-dir \
    "apache-airflow[postgres,www]==${AIRFLOW_VERSION}" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.8.txt"

# Install the rest of the app-specific requirements
RUN pip install --no-cache-dir -r /requirements.txt

# Set the working directory
WORKDIR /opt/airflow