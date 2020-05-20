# Use an official node runtime as a parent image
FROM python:3.6
ENV PYTHONUNBUFFERED 1
COPY ./config/client/entrypoint.sh .
COPY /config/client/requirements.txt .
RUN pip3 install --upgrade pip -r requirements.txt
RUN apt-get update
RUN apt-get install jq -y
RUN apt-get install net-tools
RUN apt-get install sysstat -y