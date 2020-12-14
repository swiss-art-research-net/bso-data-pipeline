FROM python:3.8
RUN apt update
RUN apt install -y openssh-server default-jre
# Install Python packages
RUN pip install date-parser-sari lxml urllib3 requests edtf tqdm rdflib sparqlwrapper

# Install x3ml Mapping engine
RUN mkdir x3ml
RUN wget https://github.com/isl/x3ml/releases/download/1.9.4/x3ml-engine-1.9.4-exejar.jar
RUN mv x3ml-engine-1.9.4-exejar.jar x3ml/x3ml-engine.exejar

# Install task runner (http://taskfile.dev)
RUN sh -c "$(curl -ssL https://taskfile.dev/install.sh)" -- -d

# Configure SSH for root access and set password
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
RUN echo "root:docker"|chpasswd
RUN service ssh restart

# Prepare directories and volumes
RUN mkdir /data
RUN mkdir /mapping
RUN mkdir /scripts
VOLUME /data
VOLUME /mapping
WORKDIR /scripts

# Start ssh service on entry
ENTRYPOINT service ssh start && tail -f /dev/null