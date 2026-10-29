#!/bin/bash
# tears down what setup.sh made so nothing keeps billing
# run it with: bash cleanup.sh

# hardcoded on purpose, so the grader's own project is never used
project=circular-beacon-508221-d7
region=us-central1
zone=us-central1-a
instance=my-sql-assignment5

gcloud config set project $project


echo "--- deleting the vms ---"
# http-client is not made by setup.sh, but delete it too if it was made for testing
# each one is checked first so a vm that was never made doesn't show an error
for vm in web-server forbidden-reporter http-client; do
    if gcloud compute instances describe $vm --zone=$zone > /dev/null 2>&1; then
        gcloud compute instances delete $vm --zone=$zone --quiet
    fi
done


echo "--- releasing the static ip ---"
gcloud compute addresses delete web-server-ip --region=$region --quiet


echo "--- removing the database watchdog ---"
gcloud scheduler jobs delete db-watchdog-hourly --location=$region --quiet
gcloud functions delete db-watchdog --region=$region --quiet


echo "--- stopping the database (not deleting it) ---"
gcloud sql instances patch $instance --activation-policy=NEVER --quiet


echo "--- revoking the application default login ---"
gcloud auth application-default revoke --quiet


echo "--- done ---"
