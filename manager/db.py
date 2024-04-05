import pymysql.cursors

def init_db(db_host, db_port):
    db_root_user = 'root'
    db_root_password = 'root' 
    db_name = 'whirlpool_testnet'
    db_user = 'testnet_user'
    db_password = 'Testnet_user123'
    charset = 'utf8mb4'

    if db_root_password is None:
        raise ValueError("MYSQL_ROOT_PASSWORD environment variable not set")

    create_database_sql = f"CREATE DATABASE IF NOT EXISTS {db_name}"
    create_user_sql = f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_password}'"
    grant_privileges_sql = f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'%' WITH GRANT OPTION"
    flush_privileges_sql = "FLUSH PRIVILEGES"

    connection = pymysql.connect(host=db_host,
                                port=db_port,
                                user=db_root_user,
                                password=db_root_password,
                                charset=charset,
                                cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            cursor.execute(create_database_sql)
            cursor.execute(create_user_sql)
            cursor.execute(grant_privileges_sql)
            cursor.execute(flush_privileges_sql)
        connection.commit()
    finally:
        connection.close()