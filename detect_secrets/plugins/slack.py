from __future__ import absolute_import

import re

from .regex import RegexPlugin


class SlackDetector(RegexPlugin):
    secret_type = 'Slack Token'
    regexes = (
        re.compile(r'xox(?:a|b|p|o|s|r)-(?:\d+-)+[a-z0-9]+', flags=re.IGNORECASE),
    )
