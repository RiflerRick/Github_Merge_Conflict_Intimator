import configparser

section = u"LAST_SUCCESSFUL_BUILD_TIMESTAMP"
# section = "DEFAULT"
config=configparser.ConfigParser()
config.read("/var/lib/jenkins/jobs/auto_merge_github_branches/gmci.properties")
print config.sections()
config.set(u"CULPRITS", "HEAD_BRANCH_CULPRIT_NAME", "hello")
for i in range(5):
    config.set(u"CULPRITS","HEAD_BRANCH_ALL_CULPRITS_NAMES", (config[u"CULPRITS"][
        "HEAD_BRANCH_ALL_CULPRITS_NAMES"] + str(i) + ", "))

f = open("gmci_temp.properties", 'w+')
config.write(f)
# config[section]
# for sections in config[section]:
#     print config[section][sections]