*** Settings ***
Resource    ../Resources/JiraAPIKeywords.robot
Library     ../Library/JiraFetchDopplerSecrets.py
Library     ../Library/JiraTaskandSubtaskIntegration.py
Library    ../Library/JiraTaskFieldsValidation.py
Library    ../Library/JiraTaskUICreation.py

Suite Setup    Setup Secrets

Documentation     E2E flow for create, update, status transition, and delete Task in JIRA

*** Test Cases ***
Jira Task and Subtask Integration Test via API and UI
    [Documentation]    Task creation and status transition via API
    ...                UI validation and summary update
    ...                Subtask creation via UI
    ...                Subtask verification via API
    [Tags]    API_UI_API

    ${issue_key}=    Create Jira Issue    ${EMAIL}    ${API_TOKEN}
    ${issue_status}=    Change Issue Status To In Progress    ${issue_key}    ${EMAIL}    ${API_TOKEN}
    Run Jira UI Flow        ${ISSUE_KEY}
    Get Subtask Details     ${ISSUE_KEY}    ${EMAIL}    ${API_TOKEN}

Jira Task fields Validation
    [Documentation]    Create a Jira task using API
    ...                Update assignee, priority, due date and comment via UI
    ...                Verify all updated fields via  API
    [Tags]    API_UI_API

    ${issue_key}=    Create Jira Issue    ${EMAIL}    ${API_TOKEN}
    ${assignee_name}    ${priority}    ${duedate}    ${label}   ${comment_text}=
    ...    Run Jira UI Flow With Fields    ${issue_key}

    Verify Issue Fields Via API
    ...    ${issue_key}
    ...    ${EMAIL}
    ...    ${API_TOKEN}
    ...    ${assignee_name}
    ...    ${priority}
    ...    ${duedate}
    ...    ${label}
    ...    ${comment_text}

Jira Issue[Task] Deletion Validation
    [Documentation]    Create a Jira issue using UI
    ...                Delete the issue using API
    ...                Verify deletion via GET API (expect 404)
    ...                Confirm issue is no longer visible in UI
    [Tags]    UI_API_UI
    ${issue_key}=    Run Jira UI Flow To Create Issue
    Log    Created issue: ${issue_key}    console=True
    Delete Jira Issue    ${issue_key}    ${EMAIL}    ${API_TOKEN}
    Run Keyword And Expect Error    *Issue not found*    Open Issue In UI    ${issue_key}
    Log    UI validation passed: Issue ${issue_key} no longer visible    console=True

Validate Status Transition On Deleted Issue_Status code 404
    [Documentation]    Negative test: transition on deleted issue should return 404
    [Tags]    NegativeTest_API
    ${issue_key}=    Create Jira Issue    ${EMAIL}    ${API_TOKEN}
    Delete Jira Issue       ${issue_key}    ${EMAIL}    ${API_TOKEN}
    Validate Transition On Deleted Issue    ${issue_key}    ${EMAIL}    ${API_TOKEN}

Validate Create Issue Without Summary_Status code 400
    [Documentation]    Negative test: creating issue without summary should return 400
    [Tags]    NegativeTest_API
    Validate Create Issue Without Summary    ${EMAIL}    ${API_TOKEN}

