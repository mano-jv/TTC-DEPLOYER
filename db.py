from pymongo import MongoClient

CONNECTION_STRING = "mongodb+srv://********/?retryWrites=true&w=majority"
client = MongoClient(CONNECTION_STRING)
db = client.get_database('TTC-DEPLOYER')
fresh_service_collection = db['FreshService']
jira_collection = db['Jira']
tickets_collection = db["Ticket"]
