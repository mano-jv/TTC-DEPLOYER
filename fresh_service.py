import pymongo
import requests

import db

### AUTHORIZATION AND HEADER SECTION
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Basic ********"
}

url = "https://trimbletransportation.freshservice.com/api/v2/changes"


def create_fresh_service(request):
    ### Build FreshService Ticket
    data, db_id, date, time = build_freshservice_ticket(request)

    ###Create a FreshService Ticket
    fresh_service_response = requests.post(
        url,
        headers=headers, json=data).json()
    ticket_id = str(fresh_service_response["change"]["id"])
    update_ticket_db(ticket_id, db_id, request, date, time)
    return "Please find your FreshService Ticket " + "https://trimbletransportation.freshservice.com/support/changes/" + ticket_id + "\n TTC Deployer will notify the approval status"


def update_ticket_db(ticket_id, db_id, request, date, time):
    space_name = request.get('originalDetectIntentRequest').get('payload').get('data').get('event').get('space').get(
        'name')
    db.tickets_collection.update_one({"_id": db_id},
                                     {"$set": {"ticket_id": ticket_id, "approval_status": 0, "space_name": space_name,
                                               "date": date, "time": time, "flag" : 0}}) ## Flag 0 indicates event is scheduler later


def gather_jira_details(user_email):
    response = db.tickets_collection.find_one({"user_email": user_email.lower()}, sort=[('_id', pymongo.DESCENDING)])
    return response["_id"], response["sprint_name"], response["test_link"], response["priority"], response[
        "release_notes"], response[
               "description"]


def build_freshservice_ticket(request):
    ### Get info from request
    query_result = request.get('queryResult')

    user_email = request.get('originalDetectIntentRequest').get('payload').get('data').get('event').get('user').get(
        'email')

    ticketdb_id, sprint_name, test_link, jira_priority, release_notes, description = gather_jira_details(user_email)
    # Default List
    default_priority = ["Low", "Medium", "High"]
    ticket_state = default_priority.index(jira_priority) + 1  ### LOW MEDIUM HIGH

    priority = ticket_state
    impact = ticket_state
    risk = ticket_state
    change_type = 1 if jira_priority in ["Low", "Medium"] else 2
    planned_start_date = query_result.get('parameters').get('date-time').get('startDateTime')
    planned_end_date = query_result.get('parameters').get('date-time').get('endDateTime')
    date, time = map(str, planned_start_date.split("+")[0].split("T"))

    ### Collect Fresh Service Details from DB
    response = db.fresh_service_collection.find_one({"email": user_email.lower()})

    data = {
        "agent_id": response["agent_id"],
        "group_id": response["group_id"],
        "priority": priority,
        "impact": impact,
        "risk": risk,
        "change_type": change_type,
        "planned_start_date": planned_start_date,
        "planned_end_date": planned_end_date,
        "subject": sprint_name,
        "department_id": response["department_id"],
        "description": description,
        "requester_id": response["requester_id"],
        "custom_fields": {
            "sector": response["sector"],
            "product": response["product"],
            "team": response["team"],
            "link_to_test_cases": test_link,
            "release_notes": release_notes,
            "status_page_update_required": "No",
            "noc_resources_needed": "No",
            "successful": "Yes"
        },
        "planning_fields": {
            "reason_for_change": {
                "description": description,
            },
            "change_impact": {
                "description": impact
            },
            "rollout_plan": {
                "description": "Rollout to previous successful deployment in spinnaker"
            },
            "backout_plan": {
                "description": "Rollout to previous successful deployment in spinnaker"
            },
            "custom_fields": {}
        }
    }
    return data, ticketdb_id, date, time
