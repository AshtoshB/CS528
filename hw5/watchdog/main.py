from googleapiclient import discovery
import functions_framework

project = "circular-beacon-508221-d7"
instance = "my-sql-assignment5"


# runs every hour, Cloud Scheduler sends a message to a pub-sub topic and that
# message is what wakes this function up
@functions_framework.cloud_event
def check_database(cloud_event):
    service = discovery.build("sqladmin", "v1beta4")

    database = service.instances().get(project=project, instance=instance).execute()

    state = database["state"]
    policy = database["settings"]["activationPolicy"]

    # one string, because cloud logging makes a separate entry out of every piece print writes
    print("database state: " + state + ", activation policy: " + policy)

    # ALWAYS means it is turned on (running or still starting up), NEVER means stopped
    if policy == "ALWAYS":
        body = {"settings": {"activationPolicy": "NEVER"}}

        service.instances().patch(project=project, instance=instance, body=body).execute()

        print("database was running, stopping it")
    else:
        print("database is already stopped")
