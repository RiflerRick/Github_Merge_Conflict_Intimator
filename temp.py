from unidiff import PatchSet
import urllib2

url = "https://api.github.com/repos/RiflerRick/BB_MCS_Test/commits/20f4c4b5f886f5ad506a37b8553399d51ef5e9ad"

headers = {
    "Accept" : "application/vnd.github.v3.diff"
}

# unfortunately requests is not helping because the documentation of the unidiff module is actully
# using the urllib2 and we are sticking to that.

print "printing for urllib2"

req_object = urllib2.Request(url, headers=headers)
diff = urllib2.urlopen(req_object)
patches = PatchSet(diff, 'utf-8')

print "patch len: {}".format(len(patches))

# this is how we check for the source and target diffs and if we find that we are good to go.

print patches[0][0].source_start
print patches[0][0].source_length
print patches[0][0].target_start
print patches[0][0].target_length