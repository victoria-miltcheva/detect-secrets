from __future__ import absolute_import

from .base import BasePlugin
from detect_secrets.core.potential_secret import PotentialSecret


class RegexPlugin(BasePlugin):
    regexes = None

    def __init__(self, **kwargs):
        if not self.regexes:
            raise ValueError('Plugins need to declare a regexes.')

    def analyze_string(self, string, line_num, filename):
        output = {}

        for result in self.secret_generator(string):
            secret = PotentialSecret(
                self.secret_type,
                filename,
                result,
                line_num,
            )
            output[secret] = secret

        return output

    def secret_generator(self, string):
        for regex in self.regexes:
            results = regex.findall(string)
            for result in results:
                yield result
