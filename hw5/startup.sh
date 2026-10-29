#!/bin/bash
# runs every time the VM boots, as root

# only install everything the first time the VM boots, the lock file
# means later reboots skip straight to starting the program
if [ ! -f /var/log/startup_already_done ]; then
    apt-get update
    apt-get install -y python3-venv

    python3 -m venv /opt/venv

    # pymysql 1.2 has a bug logging in to MySQL 8.4, so use the version before it
    /opt/venv/bin/pip install google-cloud-storage google-cloud-pubsub google-cloud-logging requests sqlalchemy "cloud-sql-python-connector[pymysql]" "pymysql<1.2"

    touch /var/log/startup_already_done
fi

# the python code is passed in as metadata called "code" when the VM is created
curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/code > /opt/main.py

# >> adds to the log instead of replacing it, so the timing lines survive a reboot
nohup /opt/venv/bin/python3 -u /opt/main.py >> /var/log/app.log 2>&1 &
