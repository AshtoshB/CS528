#!/bin/bash
# sets up everything assignment 5 needs
# run it with: bash setup.sh
# assumes the bucket from assignment 2 (assignment2_contents) already exists

# hardcoded on purpose, so the grader's own project is never used
project=circular-beacon-508221-d7
region=us-central1
zone=us-central1-a
bucket=assignment2_contents

instance=my-sql-assignment5
db_user=hw5user
db_pass=Cs528-Requests-2026

server_sa=assignment5-server@$project.iam.gserviceaccount.com
reporter_sa=assignment5-reporter@$project.iam.gserviceaccount.com
watchdog_sa=assignment5-watchdog@$project.iam.gserviceaccount.com

# work from the folder this script is in, so the file paths below always work
cd "$(dirname "$0")"

gcloud config set project $project


echo "--- turning on the apis ---"
gcloud services enable compute.googleapis.com sqladmin.googleapis.com pubsub.googleapis.com \
    logging.googleapis.com cloudfunctions.googleapis.com run.googleapis.com cloudbuild.googleapis.com \
    artifactregistry.googleapis.com eventarc.googleapis.com cloudscheduler.googleapis.com \
    iamcredentials.googleapis.com


echo "--- service accounts ---"
make_account() {
    if ! gcloud iam service-accounts describe $1@$project.iam.gserviceaccount.com > /dev/null 2>&1; then
        gcloud iam service-accounts create $1 --display-name="$2"
    fi
}

make_account assignment5-server "Assignment 5 web server"
make_account assignment5-reporter "Assignment 5 forbidden country reporter"
make_account assignment5-watchdog "Assignment 5 database watchdog"

# cloud sql client is only for reading and writing rows, cloud sql admin is only
# for the watchdog because it is the one thing that starts and stops the database
# (adding a role that is already there does nothing, so these are safe to run again)
gcloud projects add-iam-policy-binding $project --member="serviceAccount:$server_sa" --role="roles/cloudsql.client" > /dev/null
gcloud projects add-iam-policy-binding $project --member="serviceAccount:$server_sa" --role="roles/logging.logWriter" > /dev/null
gcloud storage buckets add-iam-policy-binding gs://$bucket --member="serviceAccount:$server_sa" --role="roles/storage.objectViewer" > /dev/null
gcloud projects add-iam-policy-binding $project --member="serviceAccount:$watchdog_sa" --role="roles/cloudsql.admin" > /dev/null


echo "--- pub-sub for the forbidden country reports ---"
if ! gcloud pubsub topics describe forbidden-requests > /dev/null 2>&1; then
    gcloud pubsub topics create forbidden-requests
fi

if ! gcloud pubsub subscriptions describe forbidden-requests-local > /dev/null 2>&1; then
    gcloud pubsub subscriptions create forbidden-requests-local --topic=forbidden-requests
fi

gcloud pubsub topics add-iam-policy-binding forbidden-requests --member="serviceAccount:$server_sa" --role="roles/pubsub.publisher" > /dev/null
gcloud pubsub subscriptions add-iam-policy-binding forbidden-requests-local --member="serviceAccount:$reporter_sa" --role="roles/pubsub.subscriber" > /dev/null


echo "--- database ---"
setup_database() {
    # if the instance is already there, the database and tables are in it,
    # so just turn it on and skip creating anything
    if gcloud sql instances describe $instance > /dev/null 2>&1; then
        echo "database already exists, starting it"
        gcloud sql instances patch $instance --activation-policy=ALWAYS --quiet
        return
    fi

    echo "database does not exist, creating it (this takes a while)"
    gcloud sql instances create $instance --database-version=MYSQL_8_4 --edition=enterprise \
        --cpu=4 --memory=16GB --region=$region --no-backup

    gcloud sql users create $db_user --instance=$instance --password=$db_pass

    # setup_schema.py logs in to google as the web server's service account,
    # so whoever runs this script needs permission to act as it
    account=$(gcloud config get-value account)
    gcloud iam service-accounts add-iam-policy-binding $server_sa --member="user:$account" --role="roles/iam.serviceAccountTokenCreator" > /dev/null

    # new permissions can take a minute to start working
    sleep 60

    gcloud auth application-default login --impersonate-service-account=$server_sa

    # the libraries setup_schema.py needs, pymysql 1.2 has a bug logging in to MySQL 8.4
    python3 -m venv venv
    venv/bin/pip install "cloud-sql-python-connector[pymysql]" sqlalchemy "pymysql<1.2"
    venv/bin/python setup_schema.py
}

setup_database


echo "--- static ip and firewall ---"
if ! gcloud compute addresses describe web-server-ip --region=$region > /dev/null 2>&1; then
    gcloud compute addresses create web-server-ip --region=$region
fi

server_ip=$(gcloud compute addresses describe web-server-ip --region=$region --format="value(address)")

if ! gcloud compute firewall-rules describe allow-http > /dev/null 2>&1; then
    gcloud compute firewall-rules create allow-http --allow=tcp:80 --target-tags=http-server
fi


echo "--- vms ---"
# startup.sh installs everything the first time the vm boots and starts the
# program on every boot, the python code is passed in as metadata called "code"
if ! gcloud compute instances describe web-server --zone=$zone > /dev/null 2>&1; then
    gcloud compute instances create web-server --zone=$zone --machine-type=e2-medium \
        --address=$server_ip --tags=http-server \
        --service-account=$server_sa --scopes=cloud-platform \
        --metadata-from-file=startup-script=startup.sh,code=service1/main.py
fi

if ! gcloud compute instances describe forbidden-reporter --zone=$zone > /dev/null 2>&1; then
    gcloud compute instances create forbidden-reporter --zone=$zone --machine-type=f1-micro \
        --service-account=$reporter_sa --scopes=cloud-platform \
        --metadata-from-file=startup-script=startup.sh,code=service2/main.py
fi


echo "--- database watchdog ---"
if ! gcloud pubsub topics describe db-watchdog > /dev/null 2>&1; then
    gcloud pubsub topics create db-watchdog
fi

gcloud functions deploy db-watchdog --gen2 --runtime=python312 --region=$region \
    --source=watchdog --entry-point=check_database --trigger-topic=db-watchdog \
    --service-account=$watchdog_sa

# the trigger runs as the watchdog account, so it needs permission to start the function
gcloud functions add-invoker-policy-binding db-watchdog --region=$region --member="serviceAccount:$watchdog_sa" > /dev/null

if ! gcloud scheduler jobs describe db-watchdog-hourly --location=$region > /dev/null 2>&1; then
    gcloud scheduler jobs create pubsub db-watchdog-hourly --location=$region \
        --schedule="0 * * * *" --topic=db-watchdog --message-body="check"
else
    gcloud scheduler jobs resume db-watchdog-hourly --location=$region
fi


echo "--- done ---"
echo "web server: http://$server_ip/"
echo "the watchdog stops the database at the top of every hour, pause it while you are using the database:"
echo "  gcloud scheduler jobs pause db-watchdog-hourly --location=$region"
