#!/usr/bin/env python3
"""
Lists files within a ZIP archive and calculates the SHA256 of the decompressed data.
"""

__author__ = "Lars Wallenborn"
__version__ = "1.0.0"

import argparse
from logzero import logger
import zipfile
import os
import hashlib


def main(args):
    for file_name in args.file_names:
        if not os.path.exists(file_name):
            logger.error("File with name \"%s\" does not exist" % file_name)
        zip = zipfile.ZipFile(file_name)
        if args.password:
            zip.setpassword(args.password.encode('utf-8'))

        for zipped_name in zip.namelist():
            row = []
            if len(args.file_names) > 1:
                row.append(file_name)
            row.append(zipped_name)

            try:
                zip_content = zip.read(zipped_name)
            except RuntimeError as e:
                logger.error(e)
                break
            row.append(hashlib.sha256(zip_content).hexdigest())

            print(args.separator.join(row))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_names", nargs="+", help="files to process")
    parser.add_argument("-p", "--password", action="store")
    parser.add_argument("-s", "--separator", default=";")
    parser.add_argument(
        "--version", action="version",
        version="%(prog)s (version {version})".format(version=__version__)
    )

    args = parser.parse_args()
    main(args)
