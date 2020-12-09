FROM python:3.8
RUN apt update
RUN apt install -y openssh-server
RUN pip install date-parser-sari lxml urllib3 requests edtf tqdm rdflib
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
RUN echo "root:docker"|chpasswd
RUN service ssh restart
VOLUME /scripts
VOLUME /keys
VOLUME /data
VOLUME /mapping
WORKDIR /scripts
ENTRYPOINT service ssh start && tail -f /dev/null
