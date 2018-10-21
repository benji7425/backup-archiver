# Backup archiver

Archives specified glob pattern results that have been modified since the last run. Designed to be run periodically with cron or something.

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

## Built with

- [Python 3.6](https://www.python.org/)
- [7zip](https://www.7-zip.org/download.html)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details