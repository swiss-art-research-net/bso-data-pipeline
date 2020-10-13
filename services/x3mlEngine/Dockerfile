FROM java:8
RUN mkdir x3ml
RUN wget https://github.com/isl/x3ml/releases/download/1.9.3/x3ml-engine-1.9.3-exejar.jar
RUN mv x3ml-engine-1.9.3-exejar.jar x3ml/x3ml-engine.exejar
RUN mkdir /input
RUN mkdir /output
RUN mkdir /mappings
RUN mkdir /scripts
VOLUME /input
VOLUME /output
VOLUME /mappings
ENTRYPOINT ["tail", "-f", "/dev/null"]
