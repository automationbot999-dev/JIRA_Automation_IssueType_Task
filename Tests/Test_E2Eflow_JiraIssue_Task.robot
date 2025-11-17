*** Settings ***
Resource    ../Resources/JiraAPIKeywords.robot
Library     ../Library/JiraFetchDopplerSecrets.py
Library     ../Library/JiraTaskandSubtaskIntegration.py
Library     ../Library/JiraTaskFieldsValidation.py
Library     ../Library/JiraTaskUICreation.py
Library     ../Library/JiraEpicStorySubTaskUIFlow.py
Library     ../Library/JiraEpicTaskUIFlow.py

Suite Setup    Setup Secrets

Documentation     E2E flow for creating Epic → Story → Task → Subtask in JIRA

*** Test Cases ***
# TC1============================================================
Jira Epic > User Story > Subtask Integration Test via API and UI
# ================================================================
    [Documentation]    Create Epic via API
    ...                Validate Epic on UI
    ...                Create Story under Epic via UI
    ...                Create Sub-Task under Story via API

    [Tags]    Epic_Story_Subtask_flow

    #Step 1. API: Create Epic
    ${epic_key}=    Create Jira Epic    ${EMAIL}    ${API_TOKEN}
    Log To Console    Epic created via API: ${epic_key}

    #Step 2. UI: Validate epic on UI and create story under epic
    ${story_key}=    Run Epic UI Flow    ${epic_key}
    Log To Console    Story created via UI: ${story_key}

     #Step 3. API: Create Subtask under Story
    ${subtask_key}=    Create Jira Subtask Under Story    ${story_key}    ${EMAIL}    ${API_TOKEN}
    Log To Console    Subtask created via API: ${subtask_key}

    #Step 4. clean up
    Delete Jira Issue   ${subtask_key}    Sub-task    ${EMAIL}    ${API_TOKEN}
    Delete Jira Issue   ${story_key}      Story       ${EMAIL}    ${API_TOKEN}
    Delete Jira Issue   ${epic_key}       Epic        ${EMAIL}    ${API_TOKEN}

# TC2=============================================================
Jira Epic > Task Integration Test via API and UI
# ================================================================
    [Documentation]    Create Epic via API
    ...                Validate Epic on UI
    ...                Create Task under Epic via UI

    [Tags]    Epic_Task_flow

    #Step 1. API: Create Epic
    ${epic_key}=    Create Jira Epic    ${EMAIL}    ${API_TOKEN}
    Log To Console    Epic created via API: ${epic_key}

    #Step 2. UI:Validate epic and Create Task under Epic
    ${task_key}=    Run Epic Task UI Flow    ${epic_key}
    Log To Console    Task created via UI: ${task_key}

    #Step 3. clean up
    Delete Jira Issue   ${task_key}    Task    ${EMAIL}    ${API_TOKEN}
    Delete Jira Issue   ${epic_key}    Epic        ${EMAIL}    ${API_TOKEN}

# TC3=============================================================
Jira Task Update/Edit fields via UI and validate via API
# ================================================================

    [Documentation]    Create a Jira task via API
    ...                Validate task is created in UI and Update assignee, priority and comment via UI
    ...                Verify all updated/edited fields via  API
    [Tags]    Task_Fields_Validation

    #Step 1. API: Create Task
    ${task_key}=    Create Jira Task    ${EMAIL}    ${API_TOKEN}

    #Step 2. UI: Update/Edit fields for task
    ${assignee_name}    ${priority}     ${label}   ${comment_text}=
    ...    Run Jira UI Flow With Fields    ${task_key}

    Task Fields Validation Via API
    ...    ${task_key}
    ...    ${EMAIL}
    ...    ${API_TOKEN}
    ...    ${assignee_name}
    ...    ${priority}
    ...    ${label}
    ...    ${comment_text}

    #Step 1. clean up
    Delete Jira Issue   ${task_key}    Task    ${EMAIL}    ${API_TOKEN}

# TC4===================================================================
Negative Test Validate Status Transition On Deleted Task_Status code 404
# ======================================================================

    [Documentation]    Negative test: transition on deleted issue should return 404
    [Tags]    NegativeTest

    #Step 1. API: Create Task
    ${task_key}=    Create Jira Task    ${EMAIL}    ${API_TOKEN}

    #Step 2. API: Delete Task
    Delete Jira Issue   ${task_key}    Task    ${EMAIL}    ${API_TOKEN}

    #Step 2. API: Try to change state on deleted task
    Validate Transition On Deleted Task    ${task_key}    ${EMAIL}    ${API_TOKEN}

# TC5===================================================================
Negative Test Validate Create Task Without Summary_Status code 400
# ======================================================================

    [Documentation]    Negative test: creating issue without summary should return 400
    [Tags]    NegativeTest_API
    Validate Create Task Without Summary    ${EMAIL}    ${API_TOKEN}

# TC6===================================================================
Intentional Failure Validate Create Task Without Summary
# ======================================================================

    [Documentation]    This test intentionally fails by comparing the wrong error message.
    [Tags]    NegativeTest_FailureDemo

    ${error}=    Validate Create Task Without Summary    ${EMAIL}    ${API_TOKEN}

    # INTENTIONAL FAILURE (wrong expected message)
    Should Be Equal    ${error}    Wrong expected error message