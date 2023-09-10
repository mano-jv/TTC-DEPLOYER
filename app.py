from bson.json_util import dumps
from flask import Flask, request, jsonify

import db
from jira_service import collect_jira_tickets
from fresh_service import create_fresh_service
from apscheduler.schedulers.background import BackgroundScheduler

from scheduler import check_approval_status

app = Flask(__name__)

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=check_approval_status, trigger="interval", seconds=15)
scheduler.start()


@app.route('/')  # this is the home page route
def hello_world():  # this is the home page function that generates the page code
    return "Hello World"


@app.route('/ipl/v1/fresh-service', methods=['POST', 'GET'])  # this is the route that handles fresh service request
def fresh_service_details():
    if request.method == "GET":
        query_params = request.args
        if query_params:
            # Try to convert the value to int
            query = {k: int(v) if isinstance(v, str) and v.isdigit() else v.lower() for k, v in query_params.items()}
            records_fetched = db.fresh_service_collection.find(query)
            # Check if the records are found
            if records_fetched.count() > 0:
                # Prepare the response
                return dumps(records_fetched)
            else:
                # No records are found
                return "", 404
        # If dictionary is empty
        else:
            return dumps(db.fresh_service_collection.find())
    elif request.method == "POST":
        data = request.get_json()
        record_created = db.fresh_service_collection.insert(data)
        return jsonify(str(record_created)), 201


@app.route('/ipl/v1/jira', methods=['POST', 'GET'])  # this is the route that handles Jira request
def jira_details():
    if request.method == "GET":
        query_params = request.args
        if query_params:
            # Try to convert the value to int
            query = {k: int(v) if isinstance(v, str) and v.isdigit() else v.lower() for k, v in query_params.items()}
            records_fetched = db.jira_collection.find(query)
            # Check if the records are found
            if records_fetched.count() > 0:
                # Prepare the response
                return dumps(records_fetched)
            else:
                # No records are found
                return "", 404
        # If dictionary is empty
        else:
            return dumps(db.jira_collection.find({}))
    elif request.method == "POST":
        data = request.get_json()
        record_created = db.jira_collection.insert(data)
        return jsonify(str(record_created)), 201


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    query_result = req.get('queryResult')
    if query_result.get('action') == 'Jira':
        response = collect_jira_tickets(req)
    elif query_result.get('action') == 'FreshService':
        response = create_fresh_service(req)

    return {
        "fulfillmentText": response,
        "source": "webhookdata"
    }


@app.route('/dummy', methods=['GET'])
def dummy():
    req = request.get_json(silent=True, force=True)
    collect_jira_tickets(req)
    return "name"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
