import sys

import requests
from packaging.version import parse

from detect_secrets import VERSION


def version_check():
    # check if running latest version, if not print warning
    # get latest version from GHE
    yellow = '\033[93m'
    end_yellow = '\033[0m'
    try:
        resp = requests.get(
            (
                'https://detect-secrets-client-version.s3.us-south.'
                'cloud-object-storage.appdomain.cloud/version'
            ),
            timeout=5,  # added for COS timeout
        )
        resp.raise_for_status()
        latest_version = parse(resp.text)
        current_version = parse(VERSION)
        if current_version < latest_version:
            print(
                yellow +
                'WARNING: You are running an outdated version of detect-secrets.\n',
                'Your version: %s\n' % current_version,
                'Latest version: %s\n' % latest_version,
                'See upgrade guide at',
                'https://ibm.biz/detect-secrets-how-to-upgrade\n' +
                end_yellow,
                file=sys.stderr,
            )
    except Exception:
        print(
            yellow +
            'Failed to check for newer version of detect-secrets.\n' +
            end_yellow,
            file=sys.stderr,
        )
