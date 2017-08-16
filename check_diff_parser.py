import merge_diff_parser
import subprocess
import os

path = "/var/lib/jenkins/workspace/auto_merge_github_branches/"
os.chdir(path)
subprocess.call(["git", "checkout", "origin/test_branch_20"])
subprocess.call(["git", "merge", "origin/master"])
p = subprocess.Popen(["git", "diff"], stdout=subprocess.PIPE)
diff_output, err = p.communicate()

print "printing diff output"
print diff_output

obj = merge_diff_parser.Parser(diff_output)
files = obj.get_files()
files.pop(0)
for file in files:
    print "printing file-----------"
    hunks = obj.get_hunks(file)
    for hunk in hunks:
        print "printing hunk now:---------"
        print hunk