import re

LOG_FILE_PATH = "/var/lib/jenkins/jobs/auto_merge_github_branches/builds/lastFailedBuild/log"
ERROR_LINE_REGEX = "ERROR: content conflict"

f = open(LOG_FILE_PATH, "r")
# once we open the file the real deal will be simply to read some regex from this file

error_line = ""
for line in f:
    if re.match(ERROR_LINE_REGEX, line):
        error_line = line

filepath = error_line.split(' ')[-1]

print filepath