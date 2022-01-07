FROM python:3.8

RUN apt-get -qq update && \
    apt-get -q -y upgrade && \
    apt-get install -y sudo curl wget locales && \
    rm -rf /var/lib/apt/lists/*
RUN locale-gen en_US.UTF-8

RUN apt update
RUN apt install -y default-jre
# Install Python packages
RUN pip install date-parser-sari lxml urllib3 requests edtf tqdm rdflib sari-field-definitions-generator sparqlwrapper PyYAML

# Install x3ml Mapping engine
RUN mkdir x3ml
RUN wget https://github.com/isl/x3ml/releases/download/1.9.4/x3ml-engine-1.9.4-exejar.jar
RUN mv x3ml-engine-1.9.4-exejar.jar x3ml/x3ml-engine.exejar

# Install task runner (http://taskfile.dev)
RUN sh -c "$(curl -ssL https://taskfile.dev/install.sh)" -- -d

# Prepare directories and volumes
RUN mkdir /data
RUN mkdir /mapping
RUN mkdir /scripts
RUN mkdir /static
VOLUME /data
VOLUME /mapping
VOLUME /static
WORKDIR /scripts

# Run idling
ENTRYPOINT tail -f /dev/null