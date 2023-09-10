import requests
import xlsxwriter
import db
from drive_upload import push_csv_to_drive

### AUTHORIZATION AND HEADER SECTION
headers = {
    "Accept": "application/json",
    "Authorization": "Basic **************"
}

### URL's
jira_url = "https://jira.trimble.tools/rest/agile/1.0/board/{0}/sprint/"
repo_url = "https://jira.trimble.tools/rest/dev-status/1.0/issue/detail?applicationType=stash&dataType=pullrequest&issueId="
jira_base_url = "https://jira.trimble.tools/browse/"


def collect_jira_tickets(request):
    ### Identify the jira board by team parameter
    team_name = request.get('queryResult').get('parameters').get('Teams')
    user_email = request.get('originalDetectIntentRequest').get('payload').get('data').get('event').get('user').get(
        'email')
    response = db.jira_collection.find_one({"team_name": team_name.lower()}, {"board_id": 1, "folder_id": 1})
    if response is None:
        return "Team Not Registered"
    board_id = response["board_id"]
    folder_id = response["folder_id"]

    #### OPEN CSV FILE
    file = open('Book.xlsx', "a")
    file.truncate(0)
    workbook = xlsxwriter.Workbook('Book.xlsx')
    worksheet = workbook.add_worksheet()

    ### GET : CURRENT ACTIVE SPRINT
    active_sprint = requests.get(
        jira_url.format(board_id) + "?state=active",
        headers=headers).json()
    active_sprint_id = active_sprint['values'][0]['id']
    active_sprint_name = active_sprint['values'][0]['name']
    freshservice_description = ''
    active_sprint_goal = active_sprint['values'][0]['goal']

    #### WRITE SPRINT NAME AND GOAL TO FILE
    title_cell_format = workbook.add_format({'bold': True, 'font_color': '993735', 'font_size': '16'})

    worksheet.write('F1', "SPRINT RELEASE DOCUMENTATION : " + active_sprint_name,
                    title_cell_format)
    header_cell_format = workbook.add_format(
        {'bold': True, 'font_color': '225492', 'font_size': '12', 'align': 'justify'})
    worksheet.write_row(3, 0, ["SPRINT NAME", active_sprint_name], header_cell_format)
    worksheet.write_row(4, 0, ["SPRINT GOAL", active_sprint_goal], header_cell_format)
    worksheet.write_row(6, 0, ["TICKET ID", "TITLE", "DESCRIPTION", "ISSUE TYPE", "PRIORITY", "REPOSITORY"],
                        header_cell_format)
    data_cell_format = workbook.add_format(
        {'font_size': '10', 'text_wrap': True})

    ### GET : READY TO DEPLOY TICKETS FOR CURRENT SPRINT
    tickets = requests.get(jira_url.format(board_id) + str(
        active_sprint_id) + "/issue?jql=status='Ready to deploy'", headers=headers).json()
    row = 7
    decide_priority = []
    test_link = ""
    if not tickets['issues']:
        return "No Tickets are available in ready to prod state"
    for ticket in tickets['issues']:
        ticket_uuid = ticket["id"]  ### RANDOM ASSIGNED ID
        ticket_id = ticket["key"]  ###TCSC-*****
        issue_type = ticket["fields"]["issuetype"]["name"]  ### BUG STORY TASK....
        description = ticket["fields"]["description"]
        title = ticket["fields"]["summary"]
        priority = ticket["fields"]["priority"]["name"]
        if priority in ["Trivial", "Undecided", "Low"]:
            decide_priority.append(0)
        elif priority in ["Critical", "High"]:
            decide_priority.append(2)
        else:
            decide_priority.append(1)

        freshservice_description = freshservice_description + "\n" + title

        ###Get Repository names
        repositories = requests.get(
            repo_url + ticket_uuid,
            headers=headers).json()
        repo_names = []
        repositories_details = repositories['detail'][0]
        for repository in repositories_details['pullRequests']:
            repo_name = repository["source"]["repository"]["name"]
            repo_names.append(repo_name)
        worksheet.write_row(row, 0,
                            [jira_base_url + ticket_id, title, description, issue_type,
                             priority],
                            data_cell_format)
        worksheet.write_row(row, 5, repo_names, data_cell_format)
        row += 1
        if "PRODUCTION" in title.upper().split(" "):
            test_link = description

    priority = ["Low", "Medium", "High"][max(decide_priority)]
    worksheet.set_column(0, 4, 18)
    workbook.close()
    spread_sheet_id = push_csv_to_drive(active_sprint_name, folder_id)
    sheet_id = "https://docs.google.com/spreadsheets/d/" + str(spread_sheet_id)
    write_jira_to_db(team_name, active_sprint_name, test_link, priority, sheet_id, freshservice_description, user_email)
    return sheet_id


def write_jira_to_db(team_name, sprint_name, test_link, priority, sheet_id, description, user_email):
    data = {
        "team_name": team_name,
        "sprint_name": sprint_name,
        "test_link": test_link,
        "priority": priority,
        "release_notes": sheet_id,
        "description": description,
        "user_email": user_email
    }
    db.tickets_collection.insert_one(data)
