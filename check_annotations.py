import os
import subprocess

path = "/var/lib/jenkins/workspace/auto_merge_github_branches/"
os.chdir(path)
subprocess.call(["git", "checkout", "origin/test_branch_20"])
subprocess.call(["git", "merge", "origin/master"])
p = subprocess.Popen(["git", "annotate", "helloworld"], stdout=subprocess.PIPE)
diff, err = p.communicate()

diff_lines = diff.split("\n")

commit_authors = []
commits = []

for line in diff_lines:
    commits.append(line.split("\t")[0])

for line in diff_lines:
    a = line.split("\t")
    if len(a) > 1:
        commit_authors.append(a[1][1:])

print commit_authors

print "--------------------------"

print commits