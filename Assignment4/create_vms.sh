#!/bin/bash
# creates the web server VM and the forbidden country VM, and starts both programs

project=circular-beacon-508221-d7
zone=us-central1-a

gcloud config set project $project

gcloud compute instances create web-server \
    --zone=$zone \
    --machine-type=f1-micro \
    --address=web-server-ip \
    --tags=http-server \
    --service-account=assignment4-server@$project.iam.gserviceaccount.com \
    --scopes=cloud-platform \
    --metadata-from-file=startup-script=startup.sh,code=service1/main.py

gcloud compute instances create forbidden-reporter \
    --zone=$zone \
    --machine-type=f1-micro \
    --service-account=assignment4-reporter@$project.iam.gserviceaccount.com \
    --scopes=cloud-platform \
    --metadata-from-file=startup-script=startup.sh,code=service2/main.py
