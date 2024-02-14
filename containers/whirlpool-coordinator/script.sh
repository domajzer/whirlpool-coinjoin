#!/bin/bash

# Path to the configuration file
CONFIG_FILE="/app/whirlpool-server/config.properties"

NEW_MUST_MIX_MIN=1       # Update this value
NEW_LIQUIDITY_MIN=3      # Update this value
NEW_ANONYMITY_SET=5      # Update this value

echo "Starting Java application..."
java -jar /app/whirlpool-server/target/whirlpool-server-0.23.36.jar --spring.config.location=/app/whirlpool-server/config.properties &
JAVA_PID=$!

echo "Monitoring for stop signal..."
while [ ! -f /app/stopfile ]; do
  sleep 2
done

echo "Stop signal received. Stopping Java application..."
kill $JAVA_PID
rm -f /app/stopfile

sleep 2
echo "Executing additional script..."

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file does not exist at the specified path: $CONFIG_FILE"
    exit 1
fi

sed -i "s/\(server\.pools\[3\]\.must-mix-min = \).*/\1$NEW_MUST_MIX_MIN/" "$CONFIG_FILE"
sed -i "s/\(server\.pools\[3\]\.liquidity-min = \).*/\1$NEW_LIQUIDITY_MIN/" "$CONFIG_FILE"
sed -i "s/\(server\.pools\[3\]\.anonymity-set = \).*/\1$NEW_ANONYMITY_SET/" "$CONFIG_FILE"

echo "Configuration updated successfully."
sleep 2

java -jar /app/whirlpool-server/target/whirlpool-server-0.23.36.jar --spring.config.location=/app/whirlpool-server/config.properties
