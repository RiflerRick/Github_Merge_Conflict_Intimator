#! /home/bigbasket/.virtualenvs/githubMCI/bin/python
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
import subprocess
from unidiff import PatchSet

HEAD_BRANCH = "master"
PAT_TOKEN = github_pat_token.PAT_TOKEN

assert PAT_TOKEN
#print len(sys.argv)
assert len(sys.argv) == 5

JENKINS_HOME = sys.argv[1]
JOB_NAME = sys.argv[2]
BRANCH_NAME = sys.argv[3]
GMCI_HOME = sys.argv[4]

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
        config.read(GMCI_HOME)
        build_timestamp_key = config[u"LAST_SUCCESSFUL_BUILD_TIMESTAMP"].keys()[0]
    except Exception:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)
        # this is essential so that
        sys.exit(1)

    print "return build timestamp: {}".format(config[u"LAST_SUCCESSFUL_BUILD_TIMESTAMP"][build_timestamp_key])
    return config[u"LAST_SUCCESSFUL_BUILD_TIMESTAMP"][build_timestamp_key]


def get_conflicting_filepaths():
    """
    get the filepath of the conflicting file from the console log file of jenkins

    :return:
    """
    filepaths = []
    try:
        file = open(LOG_FILE_PATH, "r")
        error_line = ""
        for line in file:
            if re.match(ERROR_LINE_REGEX, line):
                error_line = line
                filepaths.append(error_line.split(' ')[-1][:-1])


    except Exception:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)
        # this is essential so that
        sys.exit(1)

    return filepaths


def list_commits_api_call(branch_name, conflicting_filepaths, timestamp):
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
    for path in conflicting_filepaths:
        params = {
            "sha" : branch_name,
            "path" : path,
            "since" : str(timestamp)
        }
        url = os.path.join("https://api.github.com", "repos", OWNER_NAME, REPO_NAME, "commits")
        try:
            r = requests.get(url, headers = headers, params = params)
            response = r.json()
            if type(response) == list:
                pass
            elif type(response) == dict and response.has_key("message"):
                raise Exception("API call for the following URL failed:\n{0}\nHeaders:\nsha:"
                        " {1}\npath: {2}\nsince: {3}\nERROR: {4}".format(url, branch_name,
                         path, timestamp, response["message"]))

            base_branch_response.append(response)

        except Exception as e:
            exc_type, exc_val, exc_tb = sys.exc_info()
            traceback.print_exception(exc_type, exc_val, exc_tb)
            print str(e)
            sys.exit(1)

        try :
            params["sha"] = HEAD_BRANCH
            r = requests.get(url, headers=headers, params=params)
            response = r.json()
            if type(response) == list:
                pass
            elif type(response) == dict and response.has_key("message"):
                raise Exception("API call for the following URL failed:\n{0}\nHeaders:\nsha:"
                                " {1}\npath: {2}\nsince: {3}\nERROR: {4}".format(url, "master",
                                 path, timestamp, response["message"]))

            head_branch_response.append(response)

        except Exception as e:
            exc_type, exc_val, exc_tb = sys.exc_info()
            traceback.print_exception(exc_type, exc_val, exc_tb)
            print str(e)
            sys.exit(1)

    return (head_branch_response, base_branch_response)


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
        for response in head_branch_response:
            for commit in response:
                # commit is now a dictionary
                commit_timestamp = commit["commit"]["author"]["date"]
                # commit_diff = get_diff(commit["url"])
                commit_diff = ""
                commit_author_email = commit["commit"]["author"]["email"]
                commit_author_name = commit["commit"]["author"]["name"]
                head_branch_commits.append((commit_timestamp, commit_diff, commit_author_email,
                                            commit_author_name))
        for response in base_branch_response:
            for commit in response:
                # commit is now a dictionary
                commit_timestamp = commit["commit"]["author"]["date"]
                # commit_diff = get_diff(commit["url"])
                commit_diff = ""
                commit_author_email = commit["commit"]["author"]["email"]
                commit_author_name = commit["commit"]["author"]["name"]
                base_branch_commits.append((commit_timestamp, commit_diff, commit_author_email,
                                            commit_author_name))

    except Exception:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)
        sys.exit(1)

    print "head branch commits: "
    print head_branch_commits

    print "base branch commits: "
    print base_branch_commits

    return (head_branch_commits, base_branch_commits)


def get_all_authors(head_commits, base_commits):
    """
    gets all commit authors in both the base and head branch

    :param head_commits: list
    :param base_commits: list
    :return:
    """
    all_authors = {
        "head" : [],
        "base" : []
    }
    for commit in head_commits:
        t = (commit[3], commit[2])
        all_authors["head"].append(t)

    for commit in base_commits:
        t = (commit[3], commit[2])
        all_authors["base"].append(t)

    return all_authors


def wrap_html_anchor_tag(value, url):
    """
    wraps the value in an html anchor tag

    :param value:
    :param url:
    :return:
    """
    value = '<a href="' + url + '">' + value + '</a>'
    return value


def update_properties(all_authors, head_info, base_info):
    """
    update the gmci properties file
    The properties to be updated are the following:
    [CULPRITS]
    HEAD_BRANCH_CULPRIT_NAME=""
    HEAD_BRANCH_CULPRIT_EMAIL=""
    BASE_BRANCH_CULPRIT_NAME=""
    BASE_BRANCH_CULPRIT_EMAIL=""
    HEAD_BRANCH_ALL_CULPRITS_NAMES=""
    HEAD_BRANCH_ALL_CULPRITS_EMAILS=""
    BASE_BRANCH_ALL_CULPRITS_NAMES=""
    BASE_BRANCH_ALL_CULPRITS_EMAILS=""

    The structure of the head_info and base_info parameters are:
    head_info = {
        "names" : [],
        "emails" : [],
        "commits" : []
    }
    base_info = {
        "names" : [],
        "emails" : [],
        "commits" : []
    }

    :param all_authors:
    :param conflicting_authors:
    :param head_info: info on conflicting commits in head
    :param base_info: info on conflicting commits in base
    :return:
    """
    head_all_authors = all_authors["head"]
    base_all_authors = all_authors["base"]
    generic_commit_url = os.path.join("https://github.com", OWNER_NAME, REPO_NAME, "commit")

    try:
        config = configparser.ConfigParser()
        config.read(GMCI_HOME)
        # initializing all values
        config.set(u"CULPRITS", "HEAD_BRANCH_CULPRIT_EMAILS", "")
        config.set(u"CULPRITS", "HEAD_BRANCH_CULPRIT_NAMES", "")
        config.set(u"CULPRITS", "HEAD_BRANCH_CULPRIT_COMMITS", "")

        config.set(u"CULPRITS", "BASE_BRANCH_CULPRIT_NAMES", "")
        config.set(u"CULPRITS", "BASE_BRANCH_CULPRIT_EMAILS", "")
        config.set(u"CULPRITS", "BASE_BRANCH_CULPRIT_COMMITS", "")

        config.set(u"CULPRITS", "HEAD_BRANCH_ALL_CULPRITS_NAMES", "")
        config.set(u"CULPRITS", "HEAD_BRANCH_ALL_CULPRITS_EMAILS", "")

        config.set(u"CULPRITS", "BASE_BRANCH_ALL_CULPRITS_NAMES", "")
        config.set(u"CULPRITS", "BASE_BRANCH_ALL_CULPRITS_EMAILS", "")


        # if conflicting_authors["head_commit"] != ():
        head_author_names = ""
        head_author_emails = ""
        head_author_commits = ""

        base_author_names = ""
        base_author_emails = ""
        base_author_commits = ""

        # -----------HEAD---------------------------------------------
        for name in head_info["names"]:
            head_author_names = head_author_names + name + ", "

        for email in head_info["emails"]:
            head_author_emails = head_author_emails + email + ", "

        for commit in head_info["commits"]:
            url = os.path.join(generic_commit_url, commit)
            head_author_commits = head_author_commits + wrap_html_anchor_tag(commit, url) + ", "

        # ------------BASE---------------------------------------------
        for name in base_info["names"]:
            base_author_names = base_author_names + name + ", "

        for email in base_info["emails"]:
            base_author_emails = base_author_emails + email + ", "

        for commit in base_info["commits"]:
            url = os.path.join(generic_commit_url, commit)
            base_author_commits = base_author_commits + wrap_html_anchor_tag(commit, url) + ", "

        config.set(u"CULPRITS", "HEAD_BRANCH_CULPRIT_NAMES", head_author_names)
        config.set(u"CULPRITS", "HEAD_BRANCH_CULPRIT_EMAILS", head_author_emails)
        config.set(u"CULPRITS", "HEAD_BRANCH_CULPRIT_COMMITS", head_author_commits)

        config.set(u"CULPRITS", "BASE_BRANCH_CULPRIT_NAMES", base_author_names)
        config.set(u"CULPRITS", "BASE_BRANCH_CULPRIT_EMAILS", base_author_emails)
        config.set(u"CULPRITS", "BASE_BRANCH_CULPRIT_COMMITS", base_author_commits)

        val_1 = ""
        val_2 = ""
        for author in head_all_authors:
            val_1 = val_1 + author[0] + ", "
            val_2 = val_2 + author[1] + ", "

        config.set(u"CULPRITS", "HEAD_BRANCH_ALL_CULPRITS_NAMES", val_1)
        config.set(u"CULPRITS", "HEAD_BRANCH_ALL_CULPRITS_EMAILS", val_2)

        val_1 = ""
        val_2 = ""
        for author in base_all_authors:
            val_1 = val_1 + author[0] + ", "
            val_2 = val_2 + author[1] + ", "

        config.set(u"CULPRITS", "BASE_BRANCH_ALL_CULPRITS_NAMES", val_1)
        config.set(u"CULPRITS", "BASE_BRANCH_ALL_CULPRITS_EMAILS", val_2)

        f = open(GMCI_HOME, 'w')
        config.write(f)
        f.close()

    except Exception:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)
        sys.exit(1)


def parse_diff_output(annotated_info):
    """
    parses the annotated_info for commits and returns the head and base commits

    :param annotated_info:
    :return:
    """
    non_committed_commit_sha = "00000000"
    annotated_info = annotated_info.split("\n")
    total_non_committed_commits = 0
    head_conflict_commits = []
    base_conflict_commits = []
    for line in annotated_info:
        commit  = line.split("\t")[0]
        if commit ==  non_committed_commit_sha:
            print "found non committed sha"
            total_non_committed_commits += 1
            continue
        elif total_non_committed_commits%3 == 1:
            # base found
            base_conflict_commits.append(commit)
        elif total_non_committed_commits%3 == 2:
            # head found
            head_conflict_commits.append(commit)

    print "head_commits------------------------------------------------------"
    print head_conflict_commits
    print "base commits------------------------------------------------------"
    print base_conflict_commits
    return head_conflict_commits, base_conflict_commits


def update_email_content(head_names_set, head_emails_set, base_names_set, base_emails_set, head_info, base_info):
    """
    update the file for email content
    head_info = {
        "names" : [],
        "emails" : [],
        "commits" : []
    }
    base_info = {
        "names" : [],
        "emails" : [],
        "commits" : []
    }
    :param head_info:
    :param base_info:
    :return:
    """
    generic_commit_url = os.path.join("https://github.com", OWNER_NAME, REPO_NAME, "commit")

    email_content_template_path = os.path.join(JENKINS_HOME, "jobs", JOB_NAME,
                                               "email_content_template.html")
    f = open(email_content_template_path, "w")
    background_image_filepath = \
        "https://raw.githubusercontent.com/RiflerRick/Github_Merge_Conflict_Intimator/master/git_logo_bg.jpg"
    f.write('<style>body {background-image: url("' + background_image_filepath + '");background-repeat:'
                                                                                 ' no-repeat;'
            ' background-position: center center; background-attachment: fixed;}</style>')
    f.write('<body background="' + background_image_filepath + '"><br><h2>Merge Failed</h2>')
    f.write('<p style="color:blue">The following people are causing merge conflicts</p>')
    f.write('<b style="color:red">Incoming:</b>')
    author_names = ""
    for name in head_names_set:
        author_names = author_names + name + ", "
    f.write('<p>' + author_names + '</p>')

    f.write('<b style="color:red">Current:</b>')
    author_names = ""
    for name in base_names_set:
        author_names = author_names + name + ", "
    f.write('<p>' + author_names + '</p>')

    f.write('<p style="color:blue">for the following commits:</p>')
    f.write('<b style="color:red">Incoming:</b>')
    author_commits = ""
    for commit in head_info["commits"]:
        url = os.path.join(generic_commit_url, commit)
        author_commits = author_commits + wrap_html_anchor_tag(commit, url) + ", "
    f.write('<p>' + author_commits + '</p>')

    f.write('<b style="color:red">Current:</b>')
    author_commits = ""
    for commit in base_info["commits"]:
        url = os.path.join(generic_commit_url, commit)
        author_commits = author_commits + wrap_html_anchor_tag(commit, url) + ", "
    f.write('<p>' + author_commits + '</p>')

    f.write('</body><b>Diff</b><br><br>')


def get_commit_authors(head_commits, base_commits):
    """
    gets the commit authors and emails using api calls

    :param head_commits:
    :param base_commits:
    :return:
    """
    headers = {
        "Authorization" : "token " + PAT_TOKEN
    }
    head_info = {
        "names" : [],
        "emails" : [],
        "commits" : []
    }
    base_info = {
        "names" : [],
        "emails" : [],
        "commits" : []
    }

    try:
        for commit in head_commits:
            url = os.path.join("https://api.github.com", "repos", OWNER_NAME, REPO_NAME, "commits",
                               commit)
            r = requests.get(url, headers=headers)
            response = r.json()
            head_info["names"].append(response["commit"]["author"]["name"])
            head_info["emails"].append(response["commit"]["author"]["email"])
            head_info["commits"].append(commit)

        for commit in base_commits:
            url = os.path.join("https://api.github.com", "repos", OWNER_NAME, REPO_NAME, "commits",
                               commit)
            r = requests.get(url, headers=headers)
            response = r.json()
            base_info["names"].append(response["commit"]["author"]["name"])
            base_info["emails"].append(response["commit"]["author"]["email"])
            base_info["commits"].append(commit)

        return head_info, base_info

    except Exception:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)
        sys.exit(1)


build_timestamp = get_build_timestamp()
conflicting_filepaths = get_conflicting_filepaths()

print "branch: {}".format(BRANCH_NAME)
print "build_timestamp: {}".format(build_timestamp)
print "conflicting_filepath: {}".format(str(conflicting_filepaths))

path = "/var/lib/jenkins/workspace/auto_merge_github_branches/"
os.chdir(path)
subprocess.call(["git", "checkout", "origin/test_branch_20"])
subprocess.call(["git", "merge", "origin/master"])
diff = subprocess.Popen(["git", "diff"], stdout=subprocess.PIPE)
diff_output, err = diff.communicate()

diff_output_filepath = os.path.join(JENKINS_HOME, "jobs", JOB_NAME, "diff.html")
f = open(diff_output_filepath, "w+")
f.write('<textarea rows="30" cols="70" disabled="false" style="background-color:black; color:white;">\n')
f.write(diff_output)
f.write("</textarea>\n")
f.close()

head_author_names = []
base_author_names = []
head_emails = []
base_emails = []
head_commits_all_files = []
base_commits_all_files = []
for filepath in conflicting_filepaths:
    p = subprocess.Popen(["git", "annotate", filepath], stdout=subprocess.PIPE)
    annotated_info, err = p.communicate()
    head_commits, base_commits = parse_diff_output(annotated_info)
    for commit in head_commits:
        head_commits_all_files.append(commit)
    for commit in base_commits:
        base_commits_all_files.append(commit)

# print "head_commits_all_files:------------------------------------"
# print head_commits_all_files
# print "base_commits_all_files:------------------------------------"
# print base_commits_all_files
# OKAY TILL HERE

head_info, base_info = get_commit_authors(head_commits_all_files, base_commits_all_files)

# head_branch_response, base_branch_response = list_commits_api_call(BRANCH_NAME,
#                                                                    conflicting_filepaths,
#                                                                    build_timestamp)
# head_branch_commits, base_branch_commits = parse_responses(head_branch_response, base_branch_response)
#
# all_authors = get_all_authors(head_branch_commits, base_branch_commits)

# print "head_info----------------------------------------------"
# print head_info
# print "base_info----------------------------------------------"
# print base_info
all_authors = {
        "head" : [],
        "base" : []
    }
head_names_set = set()
head_emails_set = set()
base_names_set = set()
base_emails_set = set()

for name in head_info["names"]:
    head_names_set.add(name)
for name in base_info["names"]:
    base_names_set.add(name)
for email in head_info["emails"]:
    head_emails_set.add(email)
for email in base_info["emails"]:
    base_emails_set.add(email)

update_properties(all_authors, head_info, base_info)
update_email_content(head_names_set, head_emails_set, base_names_set, base_emails_set, head_info,
                     base_info)