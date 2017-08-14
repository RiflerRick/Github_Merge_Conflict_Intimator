### Github Merge Conflict Intimator

- **Requirement:** Our requirement was that we had to intimate commit authors of conflicting 
commits in merge conflicts. Imagine there are jenkins jobs configured to actually merge branches to
 keep 2 branches up to date. Now if the jenkins jobs could be configured in such a way that we
  simply have to click a swicth and that would send emails to corresponding commit authors who are
   **culprits** of the merge conflict

Jenkins already has the functionality built inside it such that we can easily get the authors and
committers of a commits that actually broke the merge and was causing conflict. However it is not working as expected and we could not figure out any reason for this even after an entire week of tries. Hence we had to come up with a python script that would solve this problem. 

There are 2 github apis that can actually extract commits from a repository.

- The first one is called the compare commits api and is powerful as it can actually compare 2 heads of 2 branches and return all commits that one branch is ahead of after the a merge operation. So lets say that a we did a merge commit at a certain point and now for the second merge operation that we try to perform we can't do it because of a merge conflict that occurs. Now we can call this api and it will show us all commits after the successful merge commit. It does not require any headers other that the Authorization header for simply authorization for private repos. There is however a catch here. No matter how good this api is, it can only give back 250 commits. For any more commits this approach won't work.

- The second one is the good old list commits api. This requires some information which is why it is required that we actually store some information in a file in the system. The information that the api requires are:
    1. Filename of the file for which we want to get the commits.  
    2. Branch name
    3. Timestamp since which we wanna get the commits
    
#### Jenkins configuration

The following plugins will be necessary in jenkins:
1. 