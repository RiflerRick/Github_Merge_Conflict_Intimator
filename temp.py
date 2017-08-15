from unidiff import PatchSet
import urllib2
import github_pat_token

url = "https://api.github.com/repos/BigBasket/BigBasket/commits/d25e5ee955daf14b1ae2a657375fa3a8e320649e"

headers = {
    "Accept" : "application/vnd.github.v3.diff",
    "Authorization" : "token " + github_pat_token.PAT_TOKEN
}

# unfortunately requests is not helping because the documentation of the unidiff module is actully
# using the urllib2 and we are sticking to that.

print "printing for urllib2"

req_object = urllib2.Request(url, headers=headers)
diff = urllib2.urlopen(req_object)
print type(diff)
patches = PatchSet(diff, 'utf-8')

print "patch len: {}".format(len(patches))

for patch in patches:
    # print type(patch)
    print "hunk"
    for hunk in patch:
        for line in hunk:
            if line.is_added:
                print "added line: {}".format(line)
            elif line.is_removed:
                print "removed line: {}".format(line)

# print patches[0][0].source_start
# print patches[0][0].source_length
# print patches[0][0].target_start
# print patches[0][0].target_length