import glob
import json
import logging
from os.path import relpath, realpath, dirname, join, normpath, exists, getmtime, isfile
from os import walk
from subprocess import Popen, PIPE
import yaml
import re


def walk_file_tree(root_dir, manifest_name):
    logging.info("Beginning directory scan in root '{}'".format(root_dir))
    paths = []
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

            def get_normpath(path): return normpath(join(root_dir, root, path))
            def get_glob_paths(key): return [normpath(glob_path) for glob_paths in [glob.glob(
                get_normpath(pattern)) for pattern in patterns[key]] for glob_path in glob_paths]

            exclude_paths = get_glob_paths(
                "exclude") if "exclude" in patterns else []
            include_paths = [relpath(get_normpath(path), root_dir) for path in get_glob_paths(
                "include") if (not re.search(r"\.\w+$", path) and path not in exclude_paths)]

            paths += include_paths

            logging.debug("Resolved include paths {}".format(include_paths))

        for path in paths:
            rel_path = relpath(join(root_dir, path), join(root_dir, root))
            if rel_path in dirs:
                dirs.remove(rel_path)
                logging.debug("Ignoring subdirs in '{}' as it's a backup dir itself".format(
                    join(root_dir, path)))
    logging.info("Finished directory scan in root {}".format(root_dir))
    return paths


def update_archives(paths, archive_directory, archive_command):
    for path in paths:
        logging.debug("Checking result '{}' for updates".format(path))

        original_path = join(root_dir, path)
        original_m_time = getmtime(original_path)  # get the last modified time
        archive_path = join(archive_directory, path)
        archive_m_time = getmtime(
            archive_path + ".7z") if isfile(archive_path + ".7z") else - 1

        if(original_m_time > archive_m_time):
            logging.debug("Updating archive for path {}".format(path))

            # archive with 7zip
            process = Popen(
                archive_command.format(
                    archive=normpath(archive_path),
                    directory=normpath(original_path)),
                stdin=PIPE,
                stdout=PIPE,
                shell=True)

            out, err = process.communicate()
            logging.debug(out)
            if err is not None:
                logging.warning(err)
        else:
            logging.debug("No updates found for '{}'".format(path))


if __name__ == "__main__":
    # configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(
                join(dirname(realpath(__file__)), "debug.log"), encoding="utf-8"),
            logging.StreamHandler()
        ])

    # load the config file
    config = {}
    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    configurations = config["configurations"]

    logging.debug("=== BEGIN ===")

    # iterate over configurations
    for configuration in configurations:

        logging.info("Begin processing configuration '{}'".format(configuration["name"]))

        root_dir = configuration["root_search_dir"]
        manifest_name = configuration["manifest_file_name"]

        paths = walk_file_tree(root_dir, manifest_name)

        logging.debug(
            "Checking for modification to following paths: {}".format(paths))

        update_archives(paths, configuration["archive_directory"], configuration["archive_command"])

        logging.info(
            "Finished checking for modification to paths in {}".format(root_dir))
        logging.info("Done processing configuration '{}'".format(configuration["name"]))

    logging.debug("=== DONE ===")
