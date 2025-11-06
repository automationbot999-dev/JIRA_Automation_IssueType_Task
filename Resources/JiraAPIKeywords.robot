*** Settings ***
Library    RESTLibrary
Library    Collections
Library    BuiltIn
Resource   JiraVariables.robot
Library    ../Library/JiraFetchDopplerSecrets.py

*** Keywords ***

Setup Secrets
    #suppresses lower-level logs (like INFO or DEBUG) during secret initialization.
    Set Log Level    WARN
    INITIALIZE SECRETS
    #Restores the log level back to INFO after secrets are initialized
    Set Log Level    INFO

Create Jira Headers
    [Arguments]    ${content_type}=application/json
    ${headers}=    Create Dictionary
    ...    Content-Type=${content_type}
    ...    Accept=application/json
    RETURN    ${headers}

Create Jira Issue
    [Arguments]    ${email}    ${token}
    #Dynamically creates a unique request ID(Test Case ID) using the current test name
    ${request_id}=    Set Variable    create_issue_${TEST NAME}
    ${HEADERS}=       Create Jira Headers
    ${project}=       Create Dictionary    key=${PROJECT_KEY}
    ${issuetype}=     Create Dictionary    name=Task
    ${fields}=        Create Dictionary
    ...    project=${project}
    ...    summary=Automated Test Issue
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
    ${issue_key}=    Extract From Response    ${request_id}    $.key
    Log    Created Jira issue with key: ${issue_key} and summary: Automated Test Issue    console=True
    RETURN    ${issue_key}

Get Subtask Details
    [Arguments]    ${issue_key}    ${email}    ${token}
    ${request_id}=    Set Variable    get_subtasks_${issue_key}
    ${headers}=       Create Jira Headers

    Make HTTP Request
    ...    ${request_id}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}
    ...    method=GET
    ...    requestHeaders=${headers}
    ...    expectedStatusCode=200
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}

    ${subtasks}=    Extract From Response    ${request_id}    $.fields.subtasks
    ${subtasks}=    Evaluate    json.loads('''${subtasks}''')    json
    FOR    ${subtask}    IN    @{subtasks}
        ${subtask_id}=    Set Variable    ${subtask["key"]}
        ${subtask_summary}=    Set Variable    ${subtask["fields"]["summary"]}
        Log    Subtask verified via API: ${subtask_id} | Summary: ${subtask_summary}    console=True
    END

Delete Jira Issue
    [Arguments]    ${issue_key}    ${email}    ${token}
    ${delete_id}=    Set Variable    delete_${issue_key}
    ${headers}=      Create Jira Headers

    Make HTTP Request
    ...    ${delete_id}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}
    ...    method=DELETE
    ...    requestHeaders=${headers}
    ...    expectedStatusCode=204
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}
    Log    Deleted issue: ${issue_key} using API    console=True

    ${verify_id}=    Set Variable    verify_deleted_${issue_key}
    Make HTTP Request
    ...    ${verify_id}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}
    ...    method=GET
    ...    requestHeaders=${headers}
    ...    expectedStatusCode=404
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}
    Log    Verified issue ${issue_key} is deleted (404 received)    console=True

Extract From Response
    [Arguments]    ${request_id}    ${json_path}
    ${value}=    Execute RC    <<<rc, ${request_id}, body, ${json_path}>>>
    RETURN    ${value}

Extract From Header
    [Arguments]    ${request_id}    ${header_name}
    ${value}=    Execute RC    <<<rc, ${request_id}, header, ${header_name}>>>
    RETURN    ${value}

Validate Transition On Deleted Issue
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

Validate Create Issue Without Summary
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

Update Jira Issue Summary
    [Arguments]    ${issue_key}    ${new_summary}    ${email}    ${token}
    ${request_id}=    Set Variable    update_${issue_key}
    ${headers}=       Create Jira Headers
    ${fields}=        Create Dictionary    summary=${new_summary}
    ${payload}=       Create Dictionary    fields=${fields}

    Make HTTP Request
    ...    ${request_id}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}
    ...    method=PUT
    ...    requestHeaders=${headers}
    ...    requestBody=${payload}
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}
    ...    expectedStatusCode=204

    Log    Updated Jira issue ${issue_key} summary to: ${new_summary}    console=True
    #Extract From Header : Content-Type
    ${content_type}=    Extract From Header    ${request_id}    Content-Type
    Log    Content-Type extracted from header is: ${content_type}    console=True

Add Comment To Jira Issue
    [Arguments]    ${issue_key}    ${comment_text}    ${email}    ${token}
    ${request_id}=    Set Variable    comment_${issue_key}
    ${headers}=       Create Jira Headers
    ${payload}=       Create Dictionary    body=${comment_text}

    Make HTTP Request
    ...    ${request_id}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}/comment
    ...    method=POST
    ...    requestHeaders=${headers}
    ...    requestBody=${payload}
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}
    ...    expectedStatusCode=201

    Log    Added comment to Jira issue ${issue_key}: ${comment_text}    console=True

Chain And Verify Jira Status Flow
    [Arguments]    ${issue_key}    ${email}    ${token}
    ${headers}=    Create Jira Headers

    # Step 1: Get initial status
    ${status_check}=    Set Variable    status_check_${issue_key}
    Make HTTP Request
    ...    ${status_check}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}
    ...    method=GET
    ...    requestHeaders=${headers}
    ...    expectedStatusCode=200
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}
    ${initial_status}=    Extract From Response    ${status_check}    $.fields.status.name
    Log    Initial status of issue ${issue_key} is: ${initial_status}    console=True

    # Step 2: Get available transitions
    ${transitions_id}=    Set Variable    transitions_${issue_key}
    Make HTTP Request
    ...    ${transitions_id}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}/transitions
    ...    method=GET
    ...    requestHeaders=${headers}
    ...    expectedStatusCode=200
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}
    ${raw_transitions}=    Extract From Response    ${transitions_id}    $.transitions[*].name
    ${transitions}=    Evaluate    ${raw_transitions} if isinstance(${raw_transitions}, list) else json.loads(${raw_transitions})     modules=json
    Log    Available transitions for issue ${issue_key}: ${transitions}    console=True

    # Step 3: Define desired transition sequence
    @{desired_transitions}=    Create List    In Review    Done

    # Step 4: Loop through transitions if status is In Progress
    Run Keyword If    '${initial_status}' == 'In Progress'    Log    Proceeding with transitions: ${desired_transitions}    console=True
    Run Keyword If    '${initial_status}' == 'In Progress'    Run Keyword    Loop Through Transitions    ${issue_key}    ${email}    ${token}    ${transitions_id}    @{desired_transitions}
    Run Keyword If    '${initial_status}' != 'In Progress'    Log    No transitions applied. Initial status is '${initial_status}'    console=True

Loop Through Transitions
    [Arguments]    ${issue_key}    ${email}    ${token}    ${transitions_id}    @{desired_transitions}
    FOR    ${transition}    IN    @{desired_transitions}
        ${id_path}=         Set Variable    $.transitions[?(@.name=="${transition}")].id
        ${to_status_path}=  Set Variable    $.transitions[?(@.name=="${transition}")].to.name
        ${transition_id}=   Extract From Response    ${transitions_id}    ${id_path}
        ${expected_status}=     Extract From Response    ${transitions_id}    ${to_status_path}
        Run Keyword If    '${transition_id}' != ''    Apply Jira Transition And Verify    ${issue_key}    ${email}    ${token}    ${transition_id}    ${transition}    ${expected_status}
    END

Apply Jira Transition And Verify
    [Arguments]    ${issue_key}    ${email}    ${token}    ${transition_id}    ${transition_name}    ${expected_status}
    ${headers}=    Create Jira Headers

    ${payload}=    Evaluate    {"transition": {"id": ${transition_id}}}    modules=json
    ${transition_request}=    Set Variable    transition_${issue_key}
    Make HTTP Request
    ...    ${transition_request}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}/transitions
    ...    method=POST
    ...    requestHeaders=${headers}
    ...    requestBody=${payload}
    ...    expectedStatusCode=204
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}
    Log    Applied transition '${transition_name} using API' to issue ${issue_key}    console=True

    ${verify_request}=    Set Variable    status_after_${issue_key}
    Make HTTP Request
    ...    ${verify_request}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}
    ...    method=GET
    ...    requestHeaders=${headers}
    ...    expectedStatusCode=200
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}
    ${actual_status}=    Extract From Response    ${verify_request}    $.fields.status.name
    Log    Verified issue ${issue_key} is in status: ${actual_status} using API   console=True
    Should Be Equal    ${actual_status}    ${expected_status}

Change Issue Status To In Progress
    [Arguments]    ${issue_key}    ${email}    ${token}
    ${headers}=    Create Jira Headers

    ${transition_req}=    Set Variable    get_transitions_${issue_key}
    Make HTTP Request
    ...    ${transition_req}
    ...    ${BASE_URL}/rest/api/2/issue/${issue_key}/transitions
    ...    method=GET
    ...    requestHeaders=${headers}
    ...    expectedStatusCode=200
    ...    authType=Basic
    ...    username=${email}
    ...    password=${token}

    ${transition_id}=    Extract From Response    ${transition_req}    $.transitions[?(@.name=="In Progress")].id
    ${expected_status}=  Set Variable    In Progress

    Apply Jira Transition And Verify    ${issue_key}    ${email}    ${token}    ${transition_id}    In Progress    ${expected_status}


Verify Issue Fields Via API
    [Arguments]    ${issue_key}    ${email}    ${token}    ${expected_assignee}    ${expected_priority}    ${expected_duedate}    ${expected_label}     ${expected_comment}

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
    ${duedate}=     Extract From Response    ${req_id}    $.fields.duedate
    ${labels}=      Extract From Response    ${req_id}    $.fields.labels[0]
    ${comment}=     Extract From Response    ${req_id}    $.fields.comment.comments[0].body



    Should Be Equal    ${assignee}    ${expected_assignee}
    Should Be Equal    ${priority}    ${expected_priority}
    Should Be Equal    ${duedate}     ${expected_duedate}
    Should Be Equal    ${labels}      ${expected_label}
    Should be equal    ${comment}     ${expected_comment}

    Log    API verification complete:    console=True
    Log    Assignee = ${assignee}        console=True
    Log    Priority = ${priority}        console=True
    Log    Due Date = ${duedate}         console=True
    Log    Label = ${labels}             console=True
    log    comment = ${comment}            console=True


