import glob
import json
import logging
import re
from copy import deepcopy
from os import makedirs, walk
from os.path import dirname, exists, getmtime, isfile, join, normpath, realpath, relpath
from shutil import copyfile
from subprocess import PIPE, Popen
from typing import Dict, List, Optional, Tuple

import yaml


def find_all_backup_paths(
    root_search_dir_abs: str, manifest_file_name: str
) -> Tuple[List[str], List[str]]:
    """Find all the backup paths specified by any manifest file found anywhere within the root directory"""

    logging.info(f"Beginning directory scan in root '{root_search_dir_abs}'")
    manifests_abs: List[str] = []
    results_abs: List[str] = []

    # Iteratively walk the file tree
    for current_dir_abs, dirs_rel, files_rel in walk(root_search_dir_abs):
        # Remove any directories beginning with a .
        for dir in dirs_rel:
            if dir.startswith("."):
                dirs_rel.remove(dir)

        # Parse manifest file to get all the include paths
        if manifest_file_name in files_rel:
            manifests_abs.append(join(current_dir_abs, manifest_file_name))
            include_paths_abs = get_include_paths_abs(
                current_dir_abs, manifest_file_name
            )

            if include_paths_abs is None:
                continue

            results_abs += include_paths_abs

            # Remove a path from the "to-process" list if it's going to be backed up itself
            for path_abs in include_paths_abs:
                path_rel = relpath(path_abs, current_dir_abs)
                if path_rel in dirs_rel:
                    dirs_rel.remove(path_rel)
                    logging.debug(
                        f"Ignoring subdirs in '{path_abs}' as it's a backup dir itself"
                    )

    logging.info(f"Finished directory scan in root {root_search_dir_abs}")

    return (manifests_abs, results_abs)


def get_include_paths_abs(
    current_dir_abs: str, manifest_file_name: str
) -> Optional[List[str]]:
    """Parse all the paths to ultimately include from a manifest file"""

    # Load the manifest file
    manifest_path = join(current_dir_abs, manifest_file_name)
    logging.debug(f"Parsing manifest at '{manifest_path}'")
    patterns = yaml.load(open(manifest_path, "r"), Loader=yaml.FullLoader)

    if patterns is None or "include" not in patterns:
        return None

    # Define functions for parsing glob paths
    def get_normpath_abs(path_rel) -> str:
        """Get the absolute normalised path for a given path relative to the current dir"""
        return normpath(join(current_dir_abs, path_rel))

    def get_matching_paths_for_entry_abs(key) -> List[List[str]]:
        """Get all of the matching paths for each entry in the given key in the current patterns dictionary"""
        return [glob.glob(get_normpath_abs(pattern)) for pattern in patterns[key]]

    def get_matching_paths_abs(key) -> List[str]:
        """Get a flattened list of all the matching paths for a given key in the current patterns dictionary"""
        return [
            normpath(matched_path)
            for matching_paths in get_matching_paths_for_entry_abs(key)
            for matched_path in matching_paths
        ]

    # Parse all exclude paths
    exclude_paths_abs = (
        get_matching_paths_abs("exclude") if "exclude" in patterns else []
    )

    # Parse all include paths and remove any that begin with a full stop
    include_paths_unfiltered_abs = [
        matched_path
        for matched_path in get_matching_paths_abs("include")
        if not re.search(r"\.\w+$", matched_path)
    ]

    # Parse all include paths and remove any that match exclude paths
    include_paths_filtered_abs = [
        path for path in include_paths_unfiltered_abs if path not in exclude_paths_abs
    ]

    logging.debug(f"Resolved include paths {include_paths_filtered_abs}")

    return include_paths_filtered_abs


def update_archives(
    root_search_dir_abs: str,
    paths_abs: List[str],
    archive_directory: str,
    archive_command: str,
) -> None:
    """Update all the archive files for the each of the given paths"""

    # Iterate all the given paths
    for source_path_abs in paths_abs:
        logging.debug(f"Checking result '{source_path_abs}' for updates")

        # Fetch last modified times for the origin path and archive file path
        source_path_rel = relpath(source_path_abs, root_search_dir_abs)
        archive_path_abs = join(archive_directory, source_path_rel)
        archive_modified_time = (
            getmtime(archive_path_abs + ".7z")
            if isfile(archive_path_abs + ".7z")
            else -1
        )

        # Update the archive only if the origin has been modified since the archive was last written
        if get_is_contents_modified_since(source_path_abs, archive_modified_time):
            logging.debug(f"Updating archive for path {source_path_abs}")

            # Archive with 7zip
            process = Popen(
                archive_command.format(
                    archive=normpath(archive_path_abs),
                    directory=normpath(source_path_abs),
                ),
                stdin=PIPE,
                stdout=PIPE,
                shell=True,
            )

            # Handle process communication
            out, err = process.communicate()
            logging.debug(out)
            if err is not None:
                logging.warning(err)
        else:
            logging.debug(f"No updates found for '{source_path_abs}'")


def get_is_contents_modified_since(path_abs: str, target_time: float) -> bool:
    """Determine whether the contents of a directory have been modified since a given date"""

    if getmtime(path_abs) > target_time:
        return True

    for current_dir_abs, dirs_rel, files_rel in walk(path_abs):
        for file_rel in files_rel:
            file_abs = join(current_dir_abs, file_rel)
            if exists(file_abs) and getmtime(file_abs) > target_time:
                return True

        for dir_rel in dirs_rel:
            dir_abs = join(current_dir_abs, dir_rel)
            if exists(dir_abs) and getmtime(dir_abs) > target_time:
                return True

    return False


def process_configuration(configuration: Dict[str, str]):
    # Load configuration values
    configuration_name = configuration["name"]
    root_search_dir_abs = configuration["root_search_dir"]
    manifest_file_name = configuration["manifest_file_name"]
    archive_directory_abs = configuration["archive_directory"]
    archive_command_unformatted = configuration["archive_command"]

    logging.info(f"Begin processing configuration '{configuration_name}'")

    # Parse and load all the backup paths for this configuration
    manifest_results = find_all_backup_paths(root_search_dir_abs, manifest_file_name)
    manifest_paths_abs = manifest_results[0]
    paths_abs = manifest_results[1]

    logging.debug(f"Checking for modification to following paths: {paths_abs}")

    # Redact the password if included in the 7z command
    configuration_sanitized = deepcopy(configuration)
    configuration_sanitized["archive_command"] = re.sub(
        r" -p[^ ]+", " -pREDACTED", configuration_sanitized["archive_command"]
    )

    # Write the configuration to a json file in the output directory
    with open(join(archive_directory_abs, "configuration.json"), "w") as outfile:
        json.dump(configuration_sanitized, outfile)

    # Copy the manifest files to the output directory
    for source_manifest_path_abs in manifest_paths_abs:
        if exists(source_manifest_path_abs):
            source_manifest_path_rel = relpath(
                source_manifest_path_abs, root_search_dir_abs
            )
            dest_manifest_path_abs = normpath(
                join(archive_directory_abs, source_manifest_path_rel)
            )
            makedirs(dirname(dest_manifest_path_abs), exist_ok=True)
            copyfile(source_manifest_path_abs, dest_manifest_path_abs)

    # Update the archives for all the paths in this configuration
    update_archives(
        root_search_dir_abs,
        paths_abs,
        archive_directory_abs,
        archive_command_unformatted,
    )

    logging.info(
        f"Finished checking for modification to paths in {root_search_dir_abs}"
    )
    logging.info(f"Done processing configuration '{configuration_name}'")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Load the config file
    config: Dict[str, List[Dict[str, str]]] = {}
    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    configurations: List[Dict[str, str]] = config["configurations"]

    logging.debug("=== BEGIN ===")

    # Iterate over configurations
    for configuration in configurations:
        process_configuration(configuration)

    logging.debug("=== DONE ===")
