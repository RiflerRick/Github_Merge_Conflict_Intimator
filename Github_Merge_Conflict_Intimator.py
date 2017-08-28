#! /home/rajdeep/.virtualenvs/githubMCI/bin/python
"""
The script will be taking 6 command line arguments:
- $JENKINS_HOME: This environment variable will simply provide the path of the jenkins home
- $JOB_NAME: This envionrment variable will provide job name of jenkins
- Name of the branch: The branch name for which to list commits
- $GMCI_HOME: This environment variable will provide the file path for the gmci properties file defined in jenkins job configuration
- email filepath
- diff filepath
"""

import sys
import os
import traceback
import configparser
import requests
import subprocess

PAT_TOKEN = os.environ["PAT_TOKEN"]

assert PAT_TOKEN
assert len(sys.argv) == 9

JENKINS_HOME = sys.argv[1]
JOB_NAME = sys.argv[2]
GMCI_HOME = sys.argv[3]
EMAIL_FILEPATH = sys.argv[4]
MERGE_DIFF_FILEPATH = sys.argv[5]
HEAD_BRANCH = sys.argv[6]
BRANCH_NAME = sys.argv[7]

# -----------------------------------REPOSITORY CONFIGs------------------------------------
OWNER_NAME = "BigBasket"
REPO_NAME = sys.argv[8]

LOG_FILE_PATH = os.path.join(JENKINS_HOME, "jobs", JOB_NAME, "builds", "lastFailedBuild", "log")
GMCI_FILE_PATH = GMCI_HOME
ERROR_LINE_REGEX = "ERROR: content conflict"


def get_conflicting_filepaths(diff_output):
    """
    get the filepath of the conflicting file from the console log file of jenkins

    :return:
    """
    try:
        filepaths = set()
        diff_lines = diff_output.split("\n")
        for line in diff_lines:
            filepaths.add(line)

    except Exception:
        exc_type, exc_val, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_val, exc_tb)
        # this is essential so that
        sys.exit(1)

    return filepaths


def wrap_html_anchor_tag(value, url):
    """
    wraps the value in an html anchor tag

    :param value:
    :param url:
    :return:
    """
    value = '<a href="' + url + '">' + value + '</a>'
    return value


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

    # print "head_commits------------------------------------------------------"
    # print head_conflict_commits
    # print "base commits------------------------------------------------------"
    # print base_conflict_commits

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
    f.write('<p>An attempted merge from <font color="red"><b>' + HEAD_BRANCH + '</b></font> to <font'
            ' color="red"><b>' + BRANCH_NAME + '</b></font> in the repository <font color="red"><b>'+
            REPO_NAME +'</b></font> failed due to the following reason:' )
    f.write('<p>The following people are causing merge conflicts</p>')
    f.write('<h3 style="color:red">Incoming:<font color="blue"> (' + HEAD_BRANCH + ')</font></h3>')
    author_names = ""
    for name in head_names_set:
        author_names = author_names + name + ", "
    f.write('<p>' + author_names + '</p>')

    f.write('<h3 style="color:red">Current: <font color="blue">(' + BRANCH_NAME + ')</font></h3>')
    author_names = ""
    for name in base_names_set:
        author_names = author_names + name + ", "
    f.write('<p>' + author_names + '</p>')

    f.write('<p>for the following commits:</p>')
    f.write('<h3 style="color:red">Incoming: <font color="blue">(' + HEAD_BRANCH + ')</font></h3>')
    author_commits = ""
    for commit in head_info["commits"]:
        url = os.path.join(generic_commit_url, commit)
        author_commits = author_commits + wrap_html_anchor_tag(commit, url) + ", "
    f.write('<p>' + author_commits + '</p>')

    f.write('<h3 style="color:red">Current: <font color="blue">(' + BRANCH_NAME + ')</font></h3>')
    author_commits = ""
    for commit in base_info["commits"]:
        url = os.path.join(generic_commit_url, commit)
        author_commits = author_commits + wrap_html_anchor_tag(commit, url) + ", "
    f.write('<p>' + author_commits + '</p>')

    f.write('</body><b>Merge Conflict Diff</b><br><br>')


def update_recipient_list(head_emails_set, base_emails_set):
    """
    update the recipient list in emails file present in $JENKINS_HOME/jobs/$JOB_NAME

    :param head_info:
    :param base_info:
    :return:
    """
    path = EMAIL_FILEPATH
    f = open(path, "w")
    all_emails = ""
    for email in head_emails_set:
        all_emails += email + ", "

    for email in base_emails_set:
        all_emails += email + ", "

    f.write(all_emails)


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


path = os.path.join(JENKINS_HOME, "jobs", JOB_NAME, "workspace")
os.chdir(path)

subprocess.call(["git", "checkout", "origin/" + BRANCH_NAME])
subprocess.call(["git", "merge", "origin/" + HEAD_BRANCH])
diff_file_only = subprocess.Popen(["git", "diff", "--name-only"], stdout=subprocess.PIPE)
diff_output_file_only, err = diff_file_only.communicate()

if diff_output_file_only != "":
    conflicting_filepaths = get_conflicting_filepaths(diff_output_file_only)
else:
    print "No diff found. Unable to find out reason for conflict"
    sys.exit(1)

print "branch: {}".format(BRANCH_NAME)
print "conflicting_filepath: {}".format(str(conflicting_filepaths))

diff = subprocess.Popen(["git", "diff"], stdout=subprocess.PIPE)
diff_output, err = diff.communicate()

diff_output_filepath = MERGE_DIFF_FILEPATH
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


head_info, base_info = get_commit_authors(head_commits_all_files, base_commits_all_files)

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

update_recipient_list (head_emails_set, base_emails_set)
update_email_content(head_names_set, head_emails_set, base_names_set, base_emails_set, head_info,
                     base_info)