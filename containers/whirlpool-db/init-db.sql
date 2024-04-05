CREATE DATABASE IF NOT EXISTS whirlpool_testnet;
CREATE USER IF NOT EXISTS 'testnet_user'@'%' IDENTIFIED BY 'Testnet_user123';
GRANT ALL PRIVILEGES ON whirlpool_testnet.* TO 'testnet_user'@'%';
FLUSH PRIVILEGES;
