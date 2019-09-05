import glob
import json
import logging
import re
from os import walk
from os.path import (dirname, exists, getmtime, isfile, join, normpath,
                     realpath, relpath)
from subprocess import PIPE, Popen
from typing import Dict, List

import yaml


def find_all_backup_paths(root_dir: str, manifest_name: str):
    """Find all the backup paths specified by any manifest file found anywhere within the root directory"""

    logging.info("Beginning directory scan in root '{}'".format(root_dir))
    results: List[str] = []

    # Iteratively walk the file tree
    for current_dir, dirs, files in walk(root_dir):

        # Remove any directories beginning with a .
        for dir in dirs:
            if dir.startswith("."):
                dirs.remove(dir)

        # Parse manifest file to get all the include paths
        if (manifest_name in files):
            include_paths = get_include_paths(current_dir, manifest_name)

            if include_paths is None:
                continue

            results += include_paths

            # I don't remember what the purpose of this line is but I think it is important
            current_dir = relpath(current_dir, root_dir)

        # Remove a path from the "to-process" list if it's going to be backed up itself
        for path in results:
            rel_path = relpath(join(root_dir, path),
                               join(root_dir, current_dir))
            if rel_path in dirs:
                dirs.remove(rel_path)
                logging.debug("Ignoring subdirs in '{}' as it's a backup dir itself"
                              .format(join(root_dir, path)))

    logging.info("Finished directory scan in root {}".format(root_dir))

    return results


def get_include_paths(current_dir: str, manifest_name: str):
    """Parse all the paths to ultimately include from a manifest file"""

    # Load the manifest file
    manifest_path = join(current_dir, manifest_name)
    logging.debug("Parsing manifest at '{}'".format(manifest_path))
    patterns = yaml.load(open(manifest_path, "r"))

    if patterns is None or "include" not in patterns:
        return None

    # Define functions for parsing glob paths
    def get_normpath(path): return normpath(join(root_dir, current_dir, path))

    def get_glob_paths(key): return [normpath(glob_path)
                                     for glob_paths in [glob.glob(get_normpath(pattern)) for pattern in patterns[key]]
                                     for glob_path in glob_paths]

    # Parse all exclude paths
    exclude_paths = get_glob_paths(
        "exclude") if "exclude" in patterns else[]

    # Parse all include paths and remove any that match exclude paths
    include_paths = [relpath(get_normpath(path), root_dir)
                     for path in get_glob_paths("include")
                     if (not re.search(r"\.\w+$", path) and path not in exclude_paths)]

    logging.debug("Resolved include paths {}".format(include_paths))

    return include_paths


def update_archives(paths: List[str], archive_directory: str, archive_command: str):
    """Update all the archive files for the each of the given paths"""

    # Iterate all the given paths
    for path in paths:
        logging.debug("Checking result '{}' for updates".format(path))

        # Fetch last modified times for the origin path and archive file path
        original_path = join(root_dir, path)
        original_m_time = getmtime(original_path)  # Get the last modified time
        archive_path = join(archive_directory, path)
        archive_m_time = getmtime(
            archive_path + ".7z") if isfile(archive_path + ".7z") else - 1

        # Update the archive only if the origin has been modified since the archive was last written
        if(original_m_time > archive_m_time):
            logging.debug("Updating archive for path {}".format(path))

            # Archive with 7zip
            process = Popen(
                archive_command.format(
                    archive=normpath(archive_path),
                    directory=normpath(original_path)),
                stdin=PIPE,
                stdout=PIPE,
                shell=True)

            # Handle process communication
            out, err = process.communicate()
            logging.debug(out)
            if err is not None:
                logging.warning(err)
        else:
            logging.debug("No updates found for '{}'".format(path))


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(
                join(dirname(realpath(__file__)), "debug.log"), encoding="utf-8"),
            logging.StreamHandler()
        ])

    # Load the config file
    config: Dict[str, List[Dict[str, str]]] = {}
    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    configurations = config["configurations"]

    logging.debug("=== BEGIN ===")

    # Iterate over configurations
    for configuration in configurations:

        logging.info("Begin processing configuration '{}'".format(
            configuration["name"]))

        # Load configuration values
        root_dir = configuration["root_search_dir"]
        manifest_name = configuration["manifest_file_name"]

        # Parse and load all the backup paths for this configuration
        paths = find_all_backup_paths(root_dir, manifest_name)

        logging.debug("Checking for modification to following paths: {}"
                      .format(paths))

        # Update the archives for all the paths in this configuration
        update_archives(
            paths, configuration["archive_directory"], configuration["archive_command"])

        logging.info("Finished checking for modification to paths in {}"
                     .format(root_dir))
        logging.info("Done processing configuration '{}'"
                     .format(configuration["name"]))

    logging.debug("=== DONE ===")
