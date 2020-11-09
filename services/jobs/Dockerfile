FROM python:3
RUN pip install date-parser-sari lxml python3-urllib3 requests
VOLUME /scripts
VOLUME /keys
VOLUME /input
VOLUME /output
VOLUME /mapping
WORKDIR /scripts
CMD ["tail", "-f", "/dev/null"]
