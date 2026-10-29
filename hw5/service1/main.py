from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud import logging as cloud_logging
from google.cloud.sql.connector import Connector
import sqlalchemy
import threading
import json
import time

bucket_name = "assignment2_contents"
project = "circular-beacon-508221-d7"
topic_id = "forbidden-requests"
port = 80

instance = "circular-beacon-508221-d7:us-central1:my-sql-assignment5"
db_user = "hw5user"
db_pass = "Cs528-Requests-2026"
db_name = "assignment5"

# countries the US will not let us export cryptographic material to
forbidden_countries = ["north korea", "iran", "cuba", "myanmar", "iraq",
                       "libya", "sudan", "zimbabwe", "syria"]

storage_client = storage.Client(project=project)
bucket = storage_client.bucket(bucket_name)
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project, topic_id)
logger = cloud_logging.Client(project=project).logger("file-server")
connector = Connector()


def getconn():
    return connector.connect(instance, "pymysql", user=db_user, password=db_pass, db=db_name)


# pool_pre_ping checks a connection still works before using it, so the server
# keeps going if the database drops a connection during the long run
engine = sqlalchemy.create_engine("mysql+pymysql://", creator=getconn, pool_pre_ping=True)

# total seconds spent in each step, and how many times each step ran
timings = {"headers": 0, "storage": 0, "send": 0, "database": 0}
counts = {"headers": 0, "storage": 0, "send": 0, "database": 0}
requests_done = 0

# two requests can finish at the same time, so only one at a time updates the totals
timing_lock = threading.Lock()


def add_time(step, seconds):
    with timing_lock:
        timings[step] += seconds
        counts[step] += 1


def request_finished():
    global requests_done

    with timing_lock:
        requests_done += 1

        if requests_done % 1000 == 0:
            line = "after " + str(requests_done) + " requests, average ms:"

            for step in timings:
                if counts[step] > 0:
                    line += " " + step + "=" + str(round(timings[step] / counts[step] * 1000, 3))

            print(line)


def get_request_info(request):
    if request.command == "POST":
        length = int(request.headers.get("Content-Length", 0))
        body = request.rfile.read(length)

        # a POST whose body isn't json naming a file is treated as asking for
        # no file, so it gets a 404 and is recorded like any other failure
        try:
            payload = json.loads(body)
            file_name = payload["file"]
        except Exception:
            file_name = ""
    else:
        # the bucket is flat so the file name is the last piece of the path
        pieces = request.path.split("/")
        file_name = pieces[len(pieces) - 1]

    country = request.headers.get("X-country")

    is_banned = False

    if country != None and country.strip().lower() in forbidden_countries:
        is_banned = True

    # the client always sends X-time, use the current time if it's missing
    time_of_day = request.headers.get("X-time")

    if time_of_day == None:
        time_of_day = time.strftime("%Y-%m-%d %H:%M:%S")

    info = {"country": country,
            "client_ip": request.headers.get("X-client-IP"),
            "gender": request.headers.get("X-gender"),
            "age": request.headers.get("X-age"),
            "income": request.headers.get("X-income"),
            "is_banned": is_banned,
            "time_of_day": time_of_day,
            "requested_file": file_name}

    return info


def read_file(file_name):
    page = bucket.blob(file_name)

    if file_name == "" or not page.exists():
        return None

    # read it as bytes so the file goes back out exactly as it is in the bucket
    contents = b""

    with page.open("rb") as f:
        for line in f:
            contents += line

    return contents


def save_to_database(info, status):
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text(
            "INSERT INTO requests (country, client_ip, gender, age, income, is_banned, time_of_day, requested_file) "
            "VALUES (:country, :client_ip, :gender, :age, :income, :is_banned, :time_of_day, :requested_file)"),
            info)

        # requests that did not return 200 also go in their own table
        if status != 200:
            conn.execute(sqlalchemy.text(
                "INSERT INTO failed_requests (request_time, requested_file, error_code) "
                "VALUES (:request_time, :requested_file, :error_code)"),
                {"request_time": info["time_of_day"], "requested_file": info["requested_file"],
                 "error_code": status})

        conn.commit()


def publish_forbidden(country, file_name, method):
    message = {"country": country, "file": file_name, "method": method,
               "time": time.ctime()}

    data = json.dumps(message).encode("utf-8")

    future = publisher.publish(topic_path, data)
    future.result()


class Handler(BaseHTTPRequestHandler):

    def send(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        # a HEAD response is not allowed to have a body
        if self.command != "HEAD":
            self.wfile.write(body)

    def respond(self, info, status, body):
        start = time.perf_counter()
        self.send(status, body)
        add_time("send", time.perf_counter() - start)

        # the client already has its response, so the database insert doesn't slow it down
        start = time.perf_counter()

        try:
            save_to_database(info, status)
        except Exception as e:
            print("database error:", e)

        add_time("database", time.perf_counter() - start)

        request_finished()

    def serve(self):
        start = time.perf_counter()
        info = get_request_info(self)
        add_time("headers", time.perf_counter() - start)

        file_name = info["requested_file"]

        if info["is_banned"]:
            logger.log_struct({"message": "blocked request from " + info["country"],
                               "country": info["country"], "file": file_name,
                               "method": self.command, "status": 400},
                              severity="CRITICAL")

            publish_forbidden(info["country"], file_name, self.command)

            self.respond(info, 400, ("400 Permission Denied: export to " + info["country"] + " is prohibited\n").encode())
            return

        start = time.perf_counter()
        contents = read_file(file_name)
        add_time("storage", time.perf_counter() - start)

        if contents == None:
            logger.log_struct({"message": "file does not exist: " + file_name,
                               "file": file_name, "method": self.command, "status": 404},
                              severity="WARNING")

            self.respond(info, 404, ("404 Not Found: " + file_name + "\n").encode())
            return

        self.respond(info, 200, contents)

    def do_GET(self):
        self.serve()

    def do_POST(self):
        self.serve()

    def not_implemented(self):
        start = time.perf_counter()
        info = get_request_info(self)
        add_time("headers", time.perf_counter() - start)

        logger.log_struct({"message": "method not implemented: " + self.command,
                           "method": self.command, "status": 501},
                          severity="ERROR")

        self.respond(info, 501, ("501 Not Implemented: " + self.command + " is not supported\n").encode())

    def do_PUT(self):
        self.not_implemented()

    def do_DELETE(self):
        self.not_implemented()

    def do_HEAD(self):
        self.not_implemented()

    def do_CONNECT(self):
        self.not_implemented()

    def do_OPTIONS(self):
        self.not_implemented()

    def do_TRACE(self):
        self.not_implemented()

    def do_PATCH(self):
        self.not_implemented()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("", port), Handler)

    print("serving on port", port)

    server.serve_forever()
