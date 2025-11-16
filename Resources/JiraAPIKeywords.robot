*** Settings ***
Library    RESTLibrary
Library    Collections
Library    BuiltIn
Resource   JiraVariables.robot
Library    ../Library/JiraFetchDopplerSecrets.py


*** Keywords ***

# ================================================================
#  SECRETS INITIALIZATION
# ================================================================
Setup Secrets
    Set Log Level    WARN
    INITIALIZE SECRETS
    Set Log Level    INFO


# ================================================================
#  COMMON HEADERS
# ================================================================
Create Jira Headers
    [Arguments]    ${content_type}=application/json
    ${headers}=    Create Dictionary
    ...    Content-Type=${content_type}
    ...    Accept=application/json
    RETURN    ${headers}


# ================================================================
#  EXTRACT VALUE FROM HTTP RESPONSE
# ================================================================
Extract From Response
    [Arguments]    ${request_id}    ${json_path}
    ${value}=    Execute RC    <<<rc, ${request_id}, body, ${json_path}>>>
    RETURN    ${value}


# ================================================================
#  CREATE EPIC
# ================================================================
Create Jira Epic
    [Arguments]    ${email}    ${token}

    ${request_id}=    Set Variable    create_epic_API
    ${HEADERS}=       Create Jira Headers
    ${project}=       Create Dictionary    key=${PROJECT_KEY}
    ${issuetype}=     Create Dictionary    name=Epic

    ${fields}=        Create Dictionary
    ...    project=${project}
    ...    summary=Automated Epic
    ...    description=Epic created via Robot Framework
    ...    issuetype=${issuetype}

    ${payload}=       Create Dictionary    fields=${fields}

    Make HTTP Request
    ...    ${request_id}
    ...    ${BASE_URL}/rest/api/2/issue
    ...    method=POST
    ...    requestHeaders=${HEADERS}
    ...    requestBody=${payload}
    ...    expectedStatusCode=201
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}

    ${epic_key}=    Extract From Response    ${request_id}    $.key
    Log    Epic created: ${epic_key}
    RETURN    ${epic_key}

# ================================================================
#  CREATE SUBTASK UNDER STORY
# ================================================================
Create Jira Subtask Under Story
    [Arguments]    ${story_key}    ${email}    ${token}

    ${request_id}=    Set Variable    create_subtask_${story_key}
    ${HEADERS}=       Create Jira Headers

    ${project}=       Create Dictionary    key=${PROJECT_KEY}
    ${parent}=        Create Dictionary    key=${story_key}
    ${issuetype}=     Create Dictionary    id=10002    # Correct Subtask type for DEMO project

    ${fields}=        Create Dictionary
    ...    project=${project}
    ...    parent=${parent}
    ...    summary=Automated Subtask under ${story_key}
    ...    description=Subtask created via API
    ...    issuetype=${issuetype}

    ${payload}=       Create Dictionary    fields=${fields}

    Make HTTP Request
    ...    ${request_id}
    ...    ${BASE_URL}/rest/api/2/issue
    ...    method=POST
    ...    requestHeaders=${HEADERS}
    ...    requestBody=${payload}
    ...    expectedStatusCode=201
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}

    ${subtask_key}=    Extract From Response    ${request_id}    $.key
    Log    Subtask created under Story: ${subtask_key}
    RETURN    ${subtask_key}

# ================================================================
#  CREATE TASK UNDER EPIC
# ================================================================
Create Jira Task Under Epic
    [Arguments]    ${epic_key}    ${email}    ${token}

    ${request_id}=    Set Variable    create_task_under_epic_${epic_key}
    ${HEADERS}=       Create Jira Headers

    ${project}=       Create Dictionary    key=${PROJECT_KEY}
    ${parent}=        Create Dictionary    key=${epic_key}
    ${issuetype}=     Create Dictionary    name=Task

    ${fields}=        Create Dictionary
    ...    project=${project}
    ...    parent=${parent}
    ...    summary=Automated Task under Epic ${epic_key}
    ...    description=Task created via API under Epic
    ...    issuetype=${issuetype}

    ${payload}=       Create Dictionary    fields=${fields}

    Make HTTP Request
    ...    ${request_id}
    ...    ${BASE_URL}/rest/api/2/issue
    ...    method=POST
    ...    requestHeaders=${HEADERS}
    ...    requestBody=${payload}
    ...    expectedStatusCode=201
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}

    ${task_key}=    Extract From Response    ${request_id}    $.key
    Log    Task created under Epic: ${task_key}
    RETURN    ${task_key}

# ================================================================
#  DELETE JIRA ISSUE - EPIC, STORY, TASK, SUBTASK
# ================================================================
Delete Jira Issue
    [Arguments]    ${issue_key}    ${issue_type}    ${email}    ${token}

    ${request_id}=    Set Variable    delete_issue_${issue_key}
    ${HEADERS}=       Create Jira Headers

    Make HTTP Request
    ...    ${request_id}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}
    ...    method=DELETE
    ...    requestHeaders=${HEADERS}
    ...    expectedStatusCode=204
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}

    Log To Console    ${issue_type} deleted: ${issue_key}

Create Jira Task
    [Arguments]    ${email}    ${token}

    ${request_id}=    Set Variable    create_task_API
    ${HEADERS}=       Create Jira Headers
    ${project}=       Create Dictionary    key=${PROJECT_KEY}
    ${issuetype}=     Create Dictionary    name=Task
    ${fields}=        Create Dictionary
    ...    project=${project}
    ...    summary=Automated Task
    ...    description=Created via Robot Framework
    ...    issuetype=${issuetype}
    ${payload}=       Create Dictionary    fields=${fields}

    Make HTTP Request
    ...    ${request_id}
    ...    ${BASE_URL}/rest/api/2/issue
    ...    method=POST
    ...    requestHeaders=${HEADERS}
    ...    requestBody=${payload}
    ...    expectedStatusCode=201
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}

    #Extract From Response issue key : key
    ${task_key}=    Extract From Response    ${request_id}    $.key
    Log    Created Jira task with key: ${task_key} and summary: Automated Task    console=True
    RETURN    ${task_key}

Task Fields Validation Via API
    [Arguments]    ${issue_key}    ${email}    ${token}    ${expected_assignee}    ${expected_priority}     ${expected_label}     ${expected_comment}

    ${headers}=    Create Jira Headers
    ${req_id}=     Set Variable    verify_${issue_key}

    Make HTTP Request
    ...    ${req_id}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}
    ...    method=GET
    ...    requestHeaders=${headers}
    ...    expectedStatusCode=200
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}

    ${assignee}=    Extract From Response    ${req_id}    $.fields.assignee.displayName
    ${priority}=    Extract From Response    ${req_id}    $.fields.priority.name
    ${labels}=      Extract From Response    ${req_id}    $.fields.labels[0]
    ${comment}=     Extract From Response    ${req_id}    $.fields.comment.comments[0].body



    Should Be Equal    ${assignee}    ${expected_assignee}
    Should Be Equal    ${priority}    ${expected_priority}
    Should Be Equal    ${labels}      ${expected_label}
    Should be equal    ${comment}     ${expected_comment}

    Log    API verification complete:    console=True
    Log    Assignee = ${assignee}        console=True
    Log    Priority = ${priority}        console=True
    Log    Label = ${labels}             console=True
    log    comment = ${comment}          console=True


Validate Transition On Deleted Issue
    [Arguments]    ${task_key}    ${email}    ${token}
    ${request_id}=    Set Variable    transition_${issue_key}
    ${headers}=       Create Jira Headers
    ${payload}=       Evaluate    {"transition": {"id": 31}}    modules=json

    Make HTTP Request
    ...    ${request_id}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}/transitions
    ...    method=POST
    ...    requestHeaders=${headers}
    ...    requestBody=${payload}
    ...    expectedStatusCode=404
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}

    ${error}=    Extract From Response    ${request_id}    $.errorMessages[0]
    Log    Error message on transition attempt for deleted task ${task_key}: ${error}    console=True

Validate Create Task Without Summary
    [Arguments]    ${email}    ${token}
    ${request_id}=    Set Variable    missing_summary_test
    ${headers}=       Create Jira Headers
    ${project}=       Create Dictionary    key=${PROJECT_KEY}
    ${issuetype}=     Create Dictionary    name=Task
    ${fields}=        Create Dictionary
    ...    project=${project}
    ...    issuetype=${issuetype}
    ${payload}=       Create Dictionary    fields=${fields}

    Make HTTP Request
    ...    ${request_id}
    ...    ${BASE_URL}/rest/api/2/issue
    ...    method=POST
    ...    requestHeaders=${headers}
    ...    requestBody=${payload}
    ...    expectedStatusCode=400
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}

    ${error}=    Extract From Response    ${request_id}    $.errors.summary
    Log    Error message for missing summary: ${error}    console=True

Validate Transition On Deleted Task
    [Arguments]    ${issue_key}    ${email}    ${token}
    ${request_id}=    Set Variable    transition_${issue_key}
    ${headers}=       Create Jira Headers
    ${payload}=       Evaluate    {"transition": {"id": 31}}    modules=json

    Make HTTP Request
    ...    ${request_id}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}/transitions
    ...    method=POST
    ...    requestHeaders=${headers}
    ...    requestBody=${payload}
    ...    expectedStatusCode=404
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}

    ${error}=    Extract From Response    ${request_id}    $.errorMessages[0]
    Log    Error message on transition attempt for deleted issue ${issue_key}: ${error}    console=True