FROM maven:3.6.3-jdk-11
WORKDIR /app
RUN git clone https://code.samourai.io/whirlpool/whirlpool-server.git
WORKDIR /app/whirlpool-server
RUN git checkout tags/0.23.36

RUN mvn clean install -Dmaven.test.skip=true

COPY mixs.csv /app/logs/mixs.csv
COPY activity.csv /app/logs/activity.csv
COPY script.sh .
RUN chmod +x script.sh 

RUN chown -R 1000:1000 /app
USER 1000:1000

ENTRYPOINT ["./script.sh"]
