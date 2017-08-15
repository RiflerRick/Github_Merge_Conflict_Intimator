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
import traceback
import configparser
import re

assert len(sys.argv) == 4

JENKINS_HOME = sys.argv[0]
JOB_NAME = sys.argv[1]
BRANCH_NAME = sys.argv[2]
GMCI_HOME = sys.argv[3]

LOG_FILE_PATH = os.path.join(JENKINS_HOME, "jobs", JOB_NAME, "builds", "lastFailedBuild", "log")
GMCI_FILE_PATH = GMCI_HOME
ERROR_LINE_REGEX = "ERROR: content conflict"


def get_build_timestamp():
    """
    get the build timestamp from the properties file

    :return: build_timestamp
    """
    config = configparser.ConfigParser()
    try:
        config.read(LOG_FILE_PATH)
        build_timestamp_key = config["LAST_SUCCESSFUL_BUILD_TIMESTAMP"].keys()[-1]
    except Exception:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)
        # this is essential so that
        sys.exit(1)

    return config["LAST_SUCCESSFUL_BUILD_TIMESTAMP"][build_timestamp_key]


def get_conflicting_filepath():
    """
    get the filepath of the conflicting file from the console log file of jenkins

    :return:
    """
    filepath = ""
    try:
        file = open(LOG_FILE_PATH, "r")
        error_line = ""
        for line in file:
            if re.match(ERROR_LINE_REGEX, line):
                error_line = line

        filepath = error_line.split(' ')[-1]

    except Exception:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)
        # this is essential so that
        sys.exit(1)

    return filepath

