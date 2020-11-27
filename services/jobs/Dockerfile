FROM python:3.8
RUN pip install date-parser-sari lxml urllib3 requests edtf tqdm rdflib
VOLUME /scripts
VOLUME /keys
VOLUME /data
VOLUME /mapping
WORKDIR /scripts
CMD ["tail", "-f", "/dev/null"]
