#! /usr/bin/env python
"""
The script will be taking 4 command line arguments:
- $JENKINS_HOME: This environment variable will simply provide the path of the jenkins home
- $JOB_NAME: This envionrment variable will provide job name of jenkins
- Name of the branch: The branch name for which to list commits
- $GMCI_HOME: This environment variable will provide the file path for the gmci properties file defined in jenkins job configuration
"""
import github_pat_token
import dateutil.parser as dtparser, datetime
import sys
import os
import traceback
import configparser
import re
import requests, urllib2
from unidiff import PatchSet

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
    :return: a tuple containing the head_branch response list and the base_branch response list
    """
    # Getting the commits for the branch to which we are merging

    base_branch_response = []
    head_branch_response = []

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
        if type(response) == list:
            pass
        elif type(response) == dict and response.has_key("message"):
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
        if type(response) == list:
            pass
        elif type(response) == dict and response.has_key("message"):
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


def get_diff(commit_url):
    """
    For getting the diff we will have to use urllib2 for compatibility of that library with unidiff
    which will be used for parsing diff

    :param commit_url:
    :return:
    """
    headers = {
        "Authorization" : "token " + PAT_TOKEN,
        "Accept" : "application/vnd.github.v3.diff"
    }
    try:
        req_object = urllib2.Request(commit_url, headers=headers)
        diff = urllib2.urlopen(req_object)
        # here diff is of type instance and that is exactly what we need for unidiff compatibility
        return diff
    except Exception:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)


def parse_responses(head_branch_response, base_branch_response):
    """
    parses the responses to get only the information from the commits that we need.
    In our case this information is going to be:
    - timestamp of commit
    - diff of the commit
    These 2 variables will be stored in a tuple for each commit in a list of commits

    :param head_branch_response:
    :param base_branch_response:
    :return:
    """
    head_branch_commits = []
    base_branch_commits = []
    try:
        for commit in head_branch_response:
            # commit is now a dictionary
            commit_timestamp = commit["author"]["date"]
            commit_diff = get_diff(commit["url"])
            commit_author_email = commit(["author"]["email"])
            commit_author_name = commit(["author"]["name"])
            head_branch_commits.append((commit_timestamp, commit_diff, commit_author_email,
                                        commit_author_name))

        for commit in base_branch_response:
            # commit is now a dictionary
            commit_timestamp = commit["author"]["date"]
            commit_diff = get_diff(commit["url"])
            commit_author_email = commit(["author"]["email"])
            commit_author_name = commit(["author"]["name"])
            base_branch_commits.append((commit_timestamp, commit_diff, commit_author_email,
                                        commit_author_name))

    except Exception:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)
        sys.exit(1)

    return (head_branch_commits, base_branch_commits)


def compare_diffs(diff1, diff2):
    """
    compares diffs and returns True if editing has been done in the same line of the file
    else returns False.

    This is really the core of this entire script. We will use a library called unidiff to compare
    diffs and find out whether diff 1 and diff 2 have anything in common

    :param diff1:
    :param diff2:
    :return:
    """
    patches1 = PatchSet(diff1, 'utf-8')
    patches2 = PatchSet(diff2, 'utf-8')



def get_conflicting_commit(head_commits, base_commits):
    """
    get the conflicting email and author name from both head branch commits and base branch commits
    Recall that each commit block is a tuple containing (commit_timestamp, commit_diff,
     commit_author_email, commit_author_name) in the same order.

    :param head_branch_commits:
    :param base_branch_commits:
    :return: A dictionary containing the head commit author name and email and the base commit
            author name and email
    """
    pointer_head= 0
    pointer_base= 0

    conflict_authors = {
        "head_commit" : (),
        "base_commit": ()
    }

    for pointer_head in range(len(head_commits)):

        for pointer_base in range(len(base_commits)):
            head = head_commits[pointer_head]
            base = base_commits[pointer_base]

            head_timestamp = dtparser.parse(head[0])
            head_diff = head[1]

            base_timestamp = dtparser.parse(base[0])
            base_diff = base[1]
            if compare_diffs(head_diff, base_diff):
                conflict_authors["head_commit"] = (head[3], head[2])
                conflict_authors["base_commit"] = (base[3], base[2])
                return conflict_authors

