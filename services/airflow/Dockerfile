FROM python:3
RUN apt update
RUN apt install -y sshpass
RUN pip install apache-airflow
RUN export AIRFLOW_HOME=/airflow
COPY airflow.cfg /root/airflow/airflow.cfg
RUN airflow initdb
COPY entrypoint.sh /
RUN mkdir /root/.ssh
COPY ssh/config /root/.ssh/config
RUN mkdir /dags
VOLUME /dags
EXPOSE 8080
CMD ["sh", "entrypoint.sh"]