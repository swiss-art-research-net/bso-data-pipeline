FROM python:3.8

RUN apt-get -qq update && \
    apt-get -q -y upgrade && \
    apt-get install -y sudo curl wget locales && \
    rm -rf /var/lib/apt/lists/*
RUN locale-gen en_US.UTF-8

# Install Python packages
RUN pip install requests rdflib flask waitress sari-sparql-parser==0.0.5

COPY ./src /src

ENV FLASK_ENV=production
#ENV FLASK_ENV=development
ENV FLASK_APP=/src/app.py

# Expose port
EXPOSE 5000

# Run
WORKDIR /src
ENTRYPOINT python app.py
#ENTRYPOINT flask run --host=0.0.0.0