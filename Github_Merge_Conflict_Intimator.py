#! /usr/bin/env python
"""
The script will be taking 4 command line arguments:
- $JENKINS_HOME: This environment variable will simply provide the path of the jenkins home
- $JOB_NAME: This envionrment variable will provide job name of jenkins
- Name of the branch: The branch name for which to list commits
- $GMCI_HOME: This environment variable will provide the file path for the gmci properties file defined in jenkins job configuration
"""

import sys
import os
import configparser

JENKINS_HOME = sys.argv[0]
JOB_NAME = sys.argv[1]
BRANCH_NAME = sys.argv[2]
GMCI_HOME = sys.argv[3]

LOG_FILE_PATH = os.path.join(JENKINS_HOME, "jobs", JOB_NAME, "builds", "lastFailedBuild", "log")
GMCI_FILE_PATH = GMCI_HOME


def get_build_timestamp():
    """
    get the build timestamp from the properties file

    :return: build_timestamp
    """
    config = configparser.ConfigParser()
    config.read(LOG_FILE_PATH)
    build_timestamp_key = config["LAST_SUCCESSFUL_BUILD_TIMESTAMP"].keys()[-1]
    return config["LAST_SUCCESSFUL_BUILD_TIMESTAMP"][build_timestamp_key]


def get_conflicting_filepath():



