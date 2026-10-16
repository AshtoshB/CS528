#!/bin/bash
# runs every time the VM boots

apt-get update
apt-get install -y python3-venv

python3 -m venv /opt/venv
/opt/venv/bin/pip install google-cloud-storage google-cloud-pubsub google-cloud-logging requests

# the python code is passed in as metadata called "code" when the VM is created
curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/code > /opt/main.py

nohup /opt/venv/bin/python3 -u /opt/main.py > /var/log/app.log 2>&1 &
