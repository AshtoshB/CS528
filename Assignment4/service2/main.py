from google.cloud import pubsub_v1
from google.api_core import exceptions
import json

project = "circular-beacon-508221-d7"
subscription_id = "forbidden-requests-local"

subscriber = pubsub_v1.SubscriberClient()


def make_message(data):
    return ("forbidden request from " + data["country"] + " for file " + data["file"]
            + " using " + data["method"] + " at " + data["time"])


def listen():
    path = subscriber.subscription_path(project, subscription_id)

    print("listening on", subscription_id)

    while True:
        try:
            response = subscriber.pull(subscription=path, max_messages=10, timeout=20)
        except exceptions.DeadlineExceeded:
            continue

        ack_ids = []

        for received in response.received_messages:
            data = json.loads(received.message.data.decode("utf-8"))

            print("ERROR:", make_message(data))

            ack_ids.append(received.ack_id)

        if len(ack_ids) > 0:
            subscriber.acknowledge(subscription=path, ack_ids=ack_ids)


if __name__ == "__main__":
    listen()
