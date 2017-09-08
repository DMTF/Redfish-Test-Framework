# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Test-Framework/LICENSE.md

import argparse
import io
import os
import requests
import zipfile
import sys


def download_zip(subdir, zip_url):
    print('Extracting {} into {}'.format(zip_url, subdir if subdir is not None else '$PWD'))

    # Create subdirectory if specified
    if subdir is not None:
        try:
            subdir = os.path.abspath(subdir)
            if not os.path.isdir(subdir):
                os.mkdir(subdir)
        except OSError as e:
            print("Error creating target subdirectory {}, error: {}".format(subdir, e), file=sys.stderr)
            exit(1)
    else:
        subdir = os.getcwd()

    # Fetch zip
    r = None
    try:
        r = requests.get(zip_url, stream=True)
        if r.status_code != requests.codes.ok:
            print("Unable to retrieve zip at {}. Status = {}, response = {}".format(zip_url, r.status_code, r.text),
                  file=sys.stderr)
            exit(1)
    except Exception as e:
        print('Unable to retrieve zip at {}. Exception is "{}"'.format(zip_url, e), file=sys.stderr)
        exit(1)

    # Extract zip
    try:
        z = zipfile.ZipFile(io.BytesIO(r.content), mode='r')
        z.extractall(path=subdir)
    except Exception as e:
        print('Unable to extract zip from {}. Exception is "{}"'.format(zip_url, e), file=sys.stderr)
        exit(1)


def main():
    arg_parser = argparse.ArgumentParser(description='Script to fetch Redfish tools and build test framework tree')
    arg_parser.add_argument('-d', '--directory', help='target directory to populate with tests')
    args = arg_parser.parse_args()

    # TODO: Only support cwd as target?
    if args.directory is None:
        target_dir = os.getcwd()
    else:
        target_dir = args.directory
        target_dir = os.path.abspath(target_dir)
        try:
            if not os.path.isdir(target_dir):
                os.mkdir(target_dir)
        except OSError as e:
            print("Error creating target directory {}, error: {}".format(target_dir, e), file=sys.stderr)
            exit(1)

    download_list = [
        ['Schema-Validation', 'https://github.com/DMTF/Redfish-Service-Validator/archive/master.zip'],
        ['Other-Tests', 'https://github.com/DMTF/Redfish-Reference-Checker/archive/master.zip'],
        ['Other-Tests', 'https://github.com/DMTF/Redfish-Mockup-Creator/archive/master.zip'],
        ['Profile-Validation', 'https://github.com/DMTF/Redfish-Interop-Validator/archive/master.zip'],
        [None, 'https://github.com/DMTF/Redfish-Usecase-Checkers/archive/master.zip']
    ]

    for subdir, zip_url in download_list:
        download_zip(subdir, zip_url)


if __name__ == "__main__":
    main()