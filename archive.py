import glob
import json
import logging
from os.path import relpath, realpath, dirname, join, normpath, exists, getmtime, isfile
from os import walk
from subprocess import Popen, PIPE
import yaml
import re

config = {}

py_dir = dirname(realpath(__file__))
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(join(py_dir, "log"), encoding="utf-8"),
        logging.StreamHandler()
    ])

# load the config file
with open("config.json", "r") as config_file:
    config = json.load(config_file)

root_dir = config["root_search_dir"]
manifest_name = config["manifest_file_name"]
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
        include_paths = [relpath(get_normpath(path), root_dir) for path in get_glob_paths("include") if (not re.search(r"\.\w+$", path) and path not in exclude_paths)]

        paths += include_paths

        logging.debug("Resolved include paths {}".format(include_paths))

    for path in paths:
        rel_path = relpath(join(root_dir, path), join(root_dir, root))
        if rel_path in dirs:
            dirs.remove(rel_path)
            logging.debug("Ignoring subdirs in '{}' as it's a backup dir itself".format(join(root_dir, path)))
        
logging.info("Finished scanning directories")
logging.debug("Found the following paths for backup: {}".format(paths))
logging.info("Checking directories for modifications since last backup")

for path in paths:
    logging.debug("Checking result '{}' for updates".format(path))

    original_path = join(root_dir, path)
    original_m_time = getmtime(original_path)  # get the last modified time
    archive_path = join(config["archive_directory"], path)
    archive_m_time = getmtime(archive_path + ".7z") if isfile(archive_path + ".7z") else - 1
    
    if(original_m_time > archive_m_time):
        logging.debug("Updating archive for path {}".format(path))

        # archive with 7zip
        process = Popen(
            config["archive_command"].format(
                archive = normpath(archive_path),
                directory = normpath(original_path)),
            stdin=PIPE,
            stdout=PIPE,
            shell=True)

        out, err = process.communicate()
        logging.debug(out)
        if err is not None:
            logging.warning(err)
    else:
        logging.debug("No updates found for '{}'".format(path))

logging.info("Finished checking directories and updating archives")

logging.debug("=== DONE ===")