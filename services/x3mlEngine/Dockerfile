FROM java:8
RUN mkdir x3ml
RUN wget https://github.com/isl/x3ml/releases/download/1.9.4/x3ml-engine-1.9.4-exejar.jar
RUN mv x3ml-engine-1.9.4-exejar.jar x3ml/x3ml-engine.exejar
RUN mkdir /data
RUN mkdir /mappings
RUN mkdir /scripts
VOLUME /data
VOLUME /mappings
ENTRYPOINT ["tail", "-f", "/dev/null"]
