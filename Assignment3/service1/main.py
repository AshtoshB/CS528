from google.cloud import storage
from google.cloud import pubsub_v1
import functions_framework
import json
import time

bucket_name = "assignment2_contents"
project = "circular-beacon-508221-d7"
topic_id = "forbidden-requests"

# countries the US will not let us export cryptographic material to
# the country codes are in here too because the test client might send either
forbidden_countries = {
    "north korea": "North Korea", "kp": "North Korea",
    "iran": "Iran", "ir": "Iran",
    "cuba": "Cuba", "cu": "Cuba",
    "myanmar": "Myanmar", "mm": "Myanmar", "burma": "Myanmar",
    "iraq": "Iraq", "iq": "Iraq",
    "libya": "Libya", "ly": "Libya",
    "sudan": "Sudan", "sd": "Sudan",
    "zimbabwe": "Zimbabwe", "zw": "Zimbabwe",
    "syria": "Syria", "sy": "Syria"
}

storage_client = storage.Client(project=project)
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project, topic_id)


def log(severity, message, info=None):
    entry = {"severity": severity, "message": message}

    if info != None:
        for key in info:
            entry[key] = info[key]

    # the json one shows up in cloud logging as a structured log and the
    # plain one as a text log.  the plain one is built up first instead of
    # being printed with commas, because print writes every argument on its
    # own and cloud logging would make a separate entry out of each one
    plain = severity + " : " + message

    print(json.dumps(entry))
    print(plain)


def get_file_name(request):

    if request.method == "GET":
        # the bucket is flat so the file name is the last piece of the path
        pieces = request.path.split("/")

        return pieces[len(pieces) - 1]

    payload = request.get_json(silent=True)

    if payload != None and "file" in payload:
        return payload["file"].lstrip("/")

    if "file" in request.form:
        return request.form["file"].lstrip("/")

    body = request.get_data(as_text=True)

    return body.strip().lstrip("/")


def publish_forbidden(country, file_name, method, path):
    message = {"country": country, "file": file_name, "method": method,
               "path": path, "time": time.ctime()}

    data = json.dumps(message).encode("utf-8")

    future = publisher.publish(topic_path, data)
    future.result()


@functions_framework.http
def serve_file(request):
    method = request.method

    if method != "GET" and method != "POST":
        log("ERROR", "method not implemented: " + method,
            {"method": method, "status": 501})

        return "501 Not Implemented: " + method + " is not supported\n", 501

    country_header = request.headers.get("X-country", "")
    country_key = country_header.strip().lower()

    file_name = get_file_name(request)

    if country_key in forbidden_countries:
        country = forbidden_countries[country_key]

        log("ERROR", "blocked request from " + country,
            {"country": country, "file": file_name, "method": method, "status": 400})

        try:
            publish_forbidden(country, file_name, method, request.path)
        except Exception as e:
            log("ERROR", "could not publish to pub-sub: " + str(e))

        return "400 Permission Denied: export to " + country + " is prohibited\n", 400

    if file_name == "":
        log("WARNING", "request did not name a file",
            {"method": method, "status": 404})

        return "404 Not Found: no file name supplied\n", 404

    bucket = storage_client.bucket(bucket_name)
    page = bucket.blob(file_name)

    if not page.exists():
        log("WARNING", "file does not exist: " + file_name,
            {"file": file_name, "method": method, "status": 404})

        return "404 Not Found: " + file_name + "\n", 404

    # read it as bytes so the file goes back out exactly as it is in the
    # bucket, opening it as text would turn the \r\n line endings into \n
    contents = b""

    with page.open("rb") as f:
        for line in f:
            contents += line

    return contents, 200, {"Content-Type": "text/html; charset=utf-8"}
