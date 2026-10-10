from google.cloud import storage
from google.cloud import pubsub_v1
from google.oauth2 import credentials as oauth2
from google.api_core import exceptions
import subprocess
import json

bucket_name = "assignment2_contents"
project = "circular-beacon-508221-d7"
subscription_id = "forbidden-requests-local"
service_account = "assignment3-svc@circular-beacon-508221-d7.iam.gserviceaccount.com"
log_file = "forbidden/violations.log"

# every line that belongs in the log file, so we never have to read it back
messages = []

storage_client = None
subscriber = None


def get_token():
    # ask gcloud for a short lived token that belongs to the service account
    # this works because our own account has serviceAccountTokenCreator on it
    command = "gcloud auth print-access-token --impersonate-service-account=" + service_account

    token = subprocess.check_output(command, shell=True, text=True)

    return token.strip()


def initiate():
    global storage_client, subscriber

    token = get_token()
    creds = oauth2.Credentials(token)

    storage_client = storage.Client(project=project, credentials=creds)
    subscriber = pubsub_v1.SubscriberClient(credentials=creds)


def load_old_messages():
    bucket = storage_client.bucket(bucket_name)
    page = bucket.blob(log_file)

    if not page.exists():
        return

    with page.open("r") as f:
        for line in f:
            line = line.strip()

            if line != "":
                messages.append(line)


def make_message(data):
    return ("forbidden request from " + data["country"] + " for file " + data["file"]
            + " using " + data["method"] + " at " + data["time"])


def append_to_bucket(line):
    # objects in a bucket cannot be appended to, so keep every message in a
    # list and write the whole list back each time.  reading the file before
    # every write is what was losing lines: the bucket is readable by anyone
    # so google is allowed to hand back a cached copy that is missing the
    # line we wrote the time before
    messages.append(line)

    bucket = storage_client.bucket(bucket_name)
    page = bucket.blob(log_file)

    # ask google not to cache the file
    page.cache_control = "no-store"

    with page.open("w", content_type="text/plain") as f:
        for message in messages:
            f.write(message + "\n")


def listen():
    path = subscriber.subscription_path(project, subscription_id)

    print("listening on", subscription_id, "as", service_account)

    while True:
        try:
            response = subscriber.pull(subscription=path, max_messages=10, timeout=20)
        except exceptions.DeadlineExceeded:
            continue

        ack_ids = []

        for received in response.received_messages:
            data = json.loads(received.message.data.decode("utf-8"))

            message = make_message(data)

            print("ERROR:", message)

            try:
                append_to_bucket(message)
            except Exception as e:
                print("error writing to bucket:", e)

            ack_ids.append(received.ack_id)

        if len(ack_ids) > 0:
            subscriber.acknowledge(subscription=path, ack_ids=ack_ids)


if __name__ == "__main__":
    initiate()

    load_old_messages()

    print("already have", len(messages), "messages in the log file")

    listen()
