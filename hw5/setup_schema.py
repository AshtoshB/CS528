from google.cloud.sql.connector import Connector
import sqlalchemy

instance = "circular-beacon-508221-d7:us-central1:my-sql-assignment5"
db_user = "hw5user"
db_pass = "Cs528-Requests-2026"
db_name = "assignment5"

connector = Connector()


def getconn():
    return connector.connect(instance, "pymysql", user=db_user, password=db_pass)


if __name__ == "__main__":
    engine = sqlalchemy.create_engine("mysql+pymysql://", creator=getconn)

    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("CREATE DATABASE IF NOT EXISTS " + db_name))

        # every request the web server receives
        conn.execute(sqlalchemy.text(
            "CREATE TABLE IF NOT EXISTS " + db_name + ".requests ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "country VARCHAR(100), "
            "client_ip VARCHAR(45), "
            "gender VARCHAR(10), "
            "age VARCHAR(10), "
            "income VARCHAR(20), "
            "is_banned BOOLEAN, "
            "time_of_day DATETIME, "
            "requested_file VARCHAR(255))"))

        # only the requests that did not return 200
        conn.execute(sqlalchemy.text(
            "CREATE TABLE IF NOT EXISTS " + db_name + ".failed_requests ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "request_time DATETIME, "
            "requested_file VARCHAR(255), "
            "error_code INT)"))

        conn.commit()

        # print the schema so it can be checked
        for table in ["requests", "failed_requests"]:
            print("table:", table)

            columns = conn.execute(sqlalchemy.text("DESCRIBE " + db_name + "." + table))

            for column in columns:
                print("   ", column[0], column[1], column[3])

    connector.close()
