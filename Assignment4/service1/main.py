from http.server import HTTPServer, BaseHTTPRequestHandler
from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud import logging as cloud_logging
import json
import time

bucket_name = "assignment2_contents"
project = "circular-beacon-508221-d7"
topic_id = "forbidden-requests"
port = 80

# countries the US will not let us export cryptographic material to
forbidden_countries = ["north korea", "iran", "cuba", "myanmar", "iraq",
                       "libya", "sudan", "zimbabwe", "syria"]

storage_client = storage.Client(project=project)
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project, topic_id)
logger = cloud_logging.Client(project=project).logger("file-server")


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

    def serve(self, file_name):
        country = self.headers.get("X-country", "")

        if country.strip().lower() in forbidden_countries:
            logger.log_struct({"message": "blocked request from " + country,
                               "country": country, "file": file_name,
                               "method": self.command, "status": 400},
                              severity="CRITICAL")

            publish_forbidden(country, file_name, self.command)

            self.send(400, ("400 Permission Denied: export to " + country + " is prohibited\n").encode())
            return

        bucket = storage_client.bucket(bucket_name)
        page = bucket.blob(file_name)

        if file_name == "" or not page.exists():
            logger.log_struct({"message": "file does not exist: " + file_name,
                               "file": file_name, "method": self.command, "status": 404},
                              severity="WARNING")

            self.send(404, ("404 Not Found: " + file_name + "\n").encode())
            return

        # read it as bytes so the file goes back out exactly as it is in the bucket
        contents = b""

        with page.open("rb") as f:
            for line in f:
                contents += line

        self.send(200, contents)

    def do_GET(self):
        # the bucket is flat so the file name is the last piece of the path
        pieces = self.path.split("/")

        self.serve(pieces[len(pieces) - 1])

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        payload = json.loads(body)

        self.serve(payload["file"])

    def not_implemented(self):
        logger.log_struct({"message": "method not implemented: " + self.command,
                           "method": self.command, "status": 501},
                          severity="ERROR")

        self.send(501, ("501 Not Implemented: " + self.command + " is not supported\n").encode())

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
    server = HTTPServer(("", port), Handler)

    print("serving on port", port)

    server.serve_forever()
