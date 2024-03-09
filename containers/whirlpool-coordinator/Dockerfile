FROM maven:3.6.3-jdk-11
WORKDIR /app
RUN git clone https://code.samourai.io/whirlpool/whirlpool-server.git
WORKDIR /app/whirlpool-server

RUN mvn clean install -Dmaven.test.skip=true

COPY custom.properties /app/whirlpool-server/config.properties
COPY mixs.csv /app/logs/mixs.csv
COPY activity.csv /app/logs/activity.csv
COPY script.sh .
RUN chmod +x script.sh 

CMD ["./script.sh"]
