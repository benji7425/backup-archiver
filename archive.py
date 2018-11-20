import glob
import json
import logging
from os.path import relpath, realpath, dirname, join, normpath, exists, getmtime
from os import walk
from subprocess import Popen, PIPE
import yaml
import re

config = {}
data = {}

py_dir = dirname(realpath(__file__))
logging.basicConfig(
    filename=join(py_dir, "log"),
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

# load the config file
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# load from existing data file
if exists(config["data_file"]):
    with open(config["data_file"], "r") as file:
        data = json.load(file)

root_dir = config["root_dir"]
manifest_name = "backup.yml"
paths = []

logging.debug("=== BEGIN ===")
logging.info("Beginning directory search in root '{}'".format(root_dir))
for root, dirs, files in walk(root_dir):
    for dir in dirs:
        if dir.startswith("."):
            dirs.remove(dir)

    if (manifest_name in files):
        logging.debug("Found manifest in '{}'".format(root))
        
        manifest_path = join(root, manifest_name)
        patterns = yaml.load(open(manifest_path, "r"))

        if patterns is None or "include" not in patterns:
            continue

        root = relpath(root, root_dir)

        get_normpath = lambda path: normpath(join(root_dir, root, path))
        get_glob_paths = lambda key: [normpath(glob_path) for glob_paths in [glob.glob(get_normpath(pattern)) for pattern in patterns[key]] for glob_path in glob_paths]

        exclude_paths = get_glob_paths("exclude") if "exclude" in patterns else []
        include_paths = [relpath(get_normpath(path), root_dir) for path in get_glob_paths("include") if path not in exclude_paths]

        paths += include_paths

        logging.debug("Resolved include paths {}".format(include_paths))

        for path in include_paths:
            rel_path = relpath(path, root)
            if rel_path in dirs:
                dirs.remove(rel_path)
                logging.debug("Ignoring subdirs in '{}' as it's a backup dir itself".format(dir))
        
logging.info("Finished scanning directories")
logging.debug("Found the following paths for backup: {}".format(paths))
logging.info("Checking directories for modifications since last backup")

for path in paths:
    logging.debug("Checking result '{}' for updates".format(path))

    full_path = join(root_dir, path)
    m_time = getmtime(full_path)  # get the last modified time
    
    # if result either not tracked yet or changed since last run, update the archive
    if path not in data or (path in data and data[path] < m_time):
        logging.debug("Updating archive for path {}".format(path))

        data[path] = m_time

        # archive with 7zip
        process = Popen(
            "{} a \"{}.zip\" \"{}\"".format(
                config["7z_path"],
                normpath(join(py_dir, config["archive_directory"], path)), # target path
                normpath(full_path)), # source path
            stdin=PIPE,
            stdout=PIPE,
            shell=True)

        out, err = process.communicate()
        logging.debug(out)
        if err is not None:
            logging.warning(err)
    else:
        logging.debug("No updates found for '{}'".format(path))

logging.debug("Writing updated modifed time data back to file")
# write back the data file
with open(config["data_file"], "w") as file:
    json.dump(data, file)

logging.debug("=== DONE ===")