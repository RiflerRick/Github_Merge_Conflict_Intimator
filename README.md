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
1. Log Trigger plugin also called post build plugin
2. Email extender plugin
3. Env inject plugin
4. Build timestamp plugin

1. Log Trigger will be used to trigger the running of the script in case the merge fails. The way the Log Trigger works is that it searches for a specified string and if found it basically runs a shell script.
2. The Email extender plugin will be used to send emails to certain people on failure.
3. Env inject plugin will enable us to inject our environment variables of choice in the entire job in jenkins. Environment variables are pretty much the only ways we can communicate between shell scripts and the plugins.
4. Build timestamp will store the build timestamp of the last successful build. 

The following line will be searched in the Log Trigger plugin:

`ERROR: Branch not suitable for integration as it does not merge cleanly`

One important idea here is that we want to catch the Exception where the branch does not merge because of a merge conflict. The concept is similar to exception handling where we do not want to handle an exception that is has too large a scope like the class `Exception`. Reading the console output and parsing it for finding out a specific output is not definitely a clean implementation to solve this issue. However we could not find a better way to handle this, other than may be writing a brand new plugin for jenkins.

There will be another log trigger that will store the build timestamp of the last successful build in a properties file whose path will be known to jenkins using the env inject plugin. Properties file are the only way we can actually inject environment variables of our choice into jenkins jobs.

The python script that will run will have the following command line arguments passed to it.
- jenkins_home
- job_name

These 2 environment variables are enough for finding out the log for the lastFailedBuild and properties file where the last successful build timestamp is stored. 
