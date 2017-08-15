#! /usr/bin/env python
"""
The script will be taking 4 command line arguments:
- $JENKINS_HOME: This environment variable will simply provide the path of the jenkins home
- $JOB_NAME: This envionrment variable will provide job name of jenkins
- Name of the branch: The branch name for which to list commits
- $GMCI_HOME: This environment variable will provide the file path for the gmci properties file defined in jenkins job configuration
"""
import github_pat_token
import sys
import os
import traceback
import configparser
import re
import requests

HEAD_BRANCH = "master"
PAT_TOKEN = github_pat_token.PAT_TOKEN

assert PAT_TOKEN
assert len(sys.argv) == 4

JENKINS_HOME = sys.argv[0]
JOB_NAME = sys.argv[1]
BRANCH_NAME = sys.argv[2]
GMCI_HOME = sys.argv[3]

# -----------------------------------REPOSITORY CONFIGs------------------------------------
OWNER_NAME = "RiflerRick"
REPO_NAME = "BB_MCS_Test"

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


def list_commits_api_call(branch_name, conflicting_filepath, timestamp):
    """
    calls the github list commits api to list all commits of a particular branch, of a particular
    file and since a particular timestamp

    :param branch_name: Branch name to check for commits
    :param conflicting_filepath: The filepath for which we need to check for commits
    :param timestamp: The time since which we need to fetch for commits.
    :return: a tuple containing the head_branch response dict and the base_branch response dict
    """
    # Getting the commits for the branch to which we are merging

    base_branch_response = {}
    head_branch_response = {}

    headers = {
        "Authorization" : "token " + PAT_TOKEN
    }
    params = {
        "sha" : branch_name,
        "path" : conflicting_filepath,
        "since" : timestamp
    }
    url = os.path.join("https://api.github.com", "repos", OWNER_NAME, REPO_NAME, "commits")
    try:
        r = requests.get(url, headers = headers, params = params)
        response = r.json()
        if response.has_key("message") == False:
            pass
        else:
            raise Exception("API call for the following URL failed:\n{0}\nHeaders:\nsha:"
                            " {1}\npath: {2}\nsince: {3}\nERROR: {4}".format(url, branch_name,                                   conflicting_filepath, timestamp, response["message"]))

        base_branch_response = response

    except Exception as e:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)
        print str(e)
        sys.exit(1)

    try:
        params["sha"] = HEAD_BRANCH
        r = requests.get(url, headers=headers, params=params)
        response = r.json()
        if response.has_key("message") == False:
            pass
        else:
            raise Exception("API call for the following URL failed:\n{0}\nHeaders:\nsha:"
                            " {1}\npath: {2}\nsince: {3}\nERROR: {4}".format(url, "master",
                             conflicting_filepath, timestamp, response["message"]))

        head_branch_response = response

    except Exception as e:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)
        print str(e)
        sys.exit(1)

    return (head_branch_response, base_branch_response)

def parse_responses(head_branch_response, base_branch_response):
    """
    parses the responses to get only the commits that we need

    :param head_branch_response:
    :param base_branch_response:
    :return:
    """



def get_conflicting_commit()





