# Backup archiver
Archives specified glob pattern results that have been modified since the last run. Designed to be run periodically with cron or something.

## Features
- Define per-dir include/exclude rules with manifest files
- Re-archives directories if they changed since the last run
- Timestamp comparisons between folder and archive - no need for a database

## Use cases
- You want to back up your files but don't want each file to be backed up individually

## Getting started
### Prerequisites
- [Python 3.6](https://www.python.org/) installed
- [Pipenv](https://pipenv.readthedocs.io/en/latest/) pip module installed
- [7zip](https://www.7-zip.org/download.html) (Windows) or [p7zip](http://p7zip.sourceforge.net/) (Linux) installed

### Setup
- Configure your settings in config.json (see [sample.config.json](./sample.config.json) for an example)
- Place *backup.yml* manifests underneath your root directory (see [sample.backup.yml](./sample.backup.yml) for an example)

- Install dependencies with `pipenv install`
- Run manually with `pipenv run main.py`  
OR
- Run with your desired task scheduler (I use [cron](https://en.wikipedia.org/wiki/Cron))

This script uses [subprocess](https://docs.python.org/3.6/library/subprocess.html) to interact with 7zip. You will need to make sure you have 7zip installed on your machine in order for this script to be able to use it.

#### Manifest rules
You can place as many *backup.yml* manifests underneath your root directory as you like, however it's up to you to make sure they don't conflict.
There are a couple of rules.

- Include and exclude paths will be parsed with [glob](https://docs.python.org/2/library/glob.html); all matching entries will be included/excluded
- Once a directory is included, it's subdirectories will not be walked, so further nested manifests will be ignored
- If include and exclude globs conflict, exclusion will take precedence; this allows various useful configurations
    - Include all directories except *cat-gifs/*
    ```
    include:
    - "*/"

    exclude:
    - "cat-gifs/"
    ```
    - Include all directories except *cat-gifs/*, but archive all *cat-gifs/* subdirectories
    ```
    include:
    - "*/"
    - "cat-gifs/*/"

    exclude:
    - "cat-gifs/"
    ```


## Built With
- [Python 3.6](https://www.python.org/)
- [7zip](https://www.7-zip.org/download.html)

## License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details