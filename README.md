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

- [Python 3.6+](https://www.python.org/) installed
- [7zip](https://www.7-zip.org/download.html) (Windows) or [p7zip](http://p7zip.sourceforge.net/) (Linux) installed


### Setup

- `pip install -r requirements.txt` as usual
- `python main.py`
- Configure your settings in config.json
- Run with your desired task scheduler (I use [cron](https://en.wikipedia.org/wiki/Cron))

This script uses [subprocess](https://docs.python.org/3.6/library/subprocess.html) to interact with 7zip. You will need to make sure you have 7zip installed on your machine in order for this script to be able to use it.

## Built With

- [Python 3.6](https://www.python.org/)
- [7zip](https://www.7-zip.org/download.html)

## Documentation

- In /docs

## Contributing

Please see [CONTRIBUTING.md](./CONTRIBUTING.md)

## Versioning

[SemVer](http://semver.org/) is used for versioning. View available versions on the [tags page](https://github.com/your/project/tags).

## Authors

- [**Benji**](https://github.com/benji7425) - *Developer*

You can also view the [contributors](https://github.com/your/project/contributors)

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details

## Acknowledgments

- README template based off [PurpleBooth's](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)