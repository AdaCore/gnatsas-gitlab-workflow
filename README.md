# GNAT SAS Gitlab workflow

This repository is both an example and set of tools to use gnatsas analysis with Gitlab

* Performs GNAT SAS analysis of each merge request
* Provides CodeQuality metrics directly on Gitlab
* Allow for manual review using GNAT Studio

## Setup

* Install the python prerequisites

```
$ pip install -r requirements.txt
```

* Make sure that GNAT Studio and GNAT SAS are in `PATH`
* Set `GITLAB_TOKEN` to the value of a private access token

## Workflow

### Create a branch

* Create the branch you want to work on
* Push your changes
* Wait for the CI analysis to run
* You can have a look at the CodeQuality results directly on GitLab
* Download the result with `python3 review.py init`
* This will show all the *unreviewed* messages

### Perform manual review using GNAT Studio

* Start GNAT Studio with the review tool: `python3 review.py edit`.
* This will place you in the GNAT SAS report view.
* Perform the reviews you want
* Close GNAT Studio
* The `gnatsas.sar` review file (in `tictactoe/gnatsas/gnatsas.outputs/gnatsas.sar`) is updated
* Commit, merge if needed, and push the file
* The new review will be available in subsequent CI analysis
