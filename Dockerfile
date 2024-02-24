FROM python:3.8
RUN apt-get update -y

COPY . /osportal
WORKDIR /osportal

RUN pip install -r requirements.txt 
RUN pip install --editable .

RUN chmod +x docker-entrypoint.sh
ENTRYPOINT ["sh", "docker-entrypoint.sh"]
