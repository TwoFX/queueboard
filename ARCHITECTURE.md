# Overall architecture of this repository

This document describes the high-level architecture of the review dashboard. If you want to familiarize yourself with the code base, you are just in the right place!

## High-level overview
This repository contains zeo separate, but related pieces of code.

The first half is infrastructure to query and download metadata about all currently open pull requests on *mathlib*, tracking their state over time. A github workflow periodically checks for updates on pull requests and downloads the current data for all pull requests with updates. Currently, this happens about every five minutes.
This data is tracked in the repository: hence, this repository also functions as a cache of information, allowing to only download meta-data for updated PRs (as opposed to download all PRs' data each time the dashboard is re-generated).

The second half contains scripts and a github workflow to generate the mathlib triage and review dashboard, using the data from the previous step. Generating this dashboard proceeds by
- generating a static webpage from this information
- publishing the webpage using github pages
These steps also are run regularly, using a cronjob. (This step happends independently of the other half of the script.) As of November 2024, a workflow run takes about two minutes, and a new job starts every five minutes. All in all, this means the data on the dashboard has a latency of around ten minutes.


## Relevant files
This section talks briefly about various important directories and data structures. Pay attention to the Architecture Invariant sections. They often talk about things which are deliberately absent in the source code.

**Part 1: data gathering infrastructure**
The `data` directory contains all downloaded data for all pull requests to the *mathlib* repository: this ought to contain data for all open pull requests. Data for closed pull requests is gradually being included (but currently, data for many such PRs is still missing).
**Invariant.** All contents in `data` is directly downloaded using the Github API. Any post-processing of data happens in a separate directory.

The `processed_data` directory contains results of data post-processing scripts. Currently, there is just one file, `aggregate_pr_data.json` (generated by `process.py`). That file contains certain overview information for each PR.

`check_data_integrity.py` is a script to verify the contents of the downloaded data: it detects broken json files and PRs whose data appears out of date. TODO document the inputs to this script!

`gather_stats.sh`: TODO document!
`gather_stats.yml`: TODO document!
`gather_stats_single.yml` currently unused; TODO document what it is meant to do!


**Part 2: generating webpages**
`dashboard.sh` (a shell script) is the main entry point:
- it queries github's API for the data above and creates a number of JSON files containing the relevant data
- it then calls `dashboard.py` (with the JSON files passed as explicit arguments) to create a dashboard.
*Currently*, all data has to be regenerated upon every call of the script.

**Architecture invariant.** All network requests happen in this script (TODO and the others!).
`dashboard.py` makes no connections to the network.

`dashboard.py` is where the core logic of creating the dashboard lives. It is a Python script, taking the JSON files from the previous step and the detailed PR information in `data` as input. It prints the HTML code for the dashboard page. It also writes the HTML code for a page "is my PR on the queue" to a separate file `on_the_queue.html`.

**Architecture invariant.** The output of `dashboard.py` only depends on its command line arguments, the contents of the `data` directory and its current time: with both fixed, it is deterministic. In particular, it makes no network requests. All I/O in that file is constrained to one method `read_user_data` in the beginning.The output of `dashboard.py` only depends on its command line arguments and its current time: with both fixed, it is deterministic. In particular, it makes no network requests.
All I/O in that file is constrained to one method `read_user_data` in the beginning.

`.github/workflows/publish-dashboard.yml` defines the workflow updating the dashboard. It runs the above scripts to generate an up-to-date dashboard, and commits the updated HTML file on the `gh-pages` branch. That branch is deployed by github pages to create the webpage.

`style.css` contains all style rules for the generated webpage
`dashboard.html` is a redirect: the dashboard used to live there, but now lives at `index.html`

`classify_pr_state.py` contains logic to classify a pull request as ready for review, awaiting action by the author, blocked on another PR, etc. This is used to generate a statistics section on the dashboard. It is called directly by `dashboard.py`.

`test` contains versions of all input files to this script, at some point in time. These can be used for locally testing `dashboard.py`.

**TODO** check if these are all files!


# Cross-cutting concerns

## Limiting github API calls
Each github API call is expensive: github (understandably) adds rate limiting to each call to its API: successive calls can happen at most once per second. This imposes a natural lower bound on the execution time of this script.
In particular, each query for each dashboard takes one second: if easily possible/the data for a particular dashboard can be easily derived (e.g., filtered) from existing data, avoiding an API call and a separate JSON file is preferred.

## Testing
There are several levels at which this project can be tested. Currently, there are no *automated* tests, but an effort is made that the dashboard logic can easily be tested manually.

- `classify_pr_state.py` has unit tests: to run them, use e.g. `nose` (which will pick them up automatically), or uncomment all methods named `test_xxx` and run `python3 classify_pr_state.py`

TODO: there are more generated HTML files now; recommend copying the folder instead...
- changes to just `dashboard.py` can be tested using the JSON files in the `test` directory: run the following from the `test` directory.
`python3 ../dashboard.py all-open-PRs-1.json all-open-PRs-2.json`.
This creates two webpages named `on_the_queue.html` and `index.html`, overwriting any previous files named thus.
You can run this command before and after your changes and compare the resulting files (using `diff` or a similar tool). Because of the overwriting, take care to copy e.g. the old version of the output to a different file before running the tool again.
(The output file needs to be in the top-level directory in order for the styling to work.)

## TODO document
- `data` directory, metadata updating via `gather_stats.sh` (and the other workflow)
- data integrity check (once written)

- additional tools for testing `mypy`, `ruff`, `isort`, (black)
