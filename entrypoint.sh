#!/bin/bash
echo "Loading .env from: $ENV_FILE_PATH"
python -c "
from dotenv import load_dotenv
import os
print('Loaded .env from:', os.getenv('ENV_FILE_PATH'))
load_dotenv(os.getenv('ENV_FILE_PATH'))
"
robot -d results Tests/Test_E2Eflow_JiraIssue_Task.robot
