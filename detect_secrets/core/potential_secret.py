import hashlib
from typing import Any
from typing import Dict
from typing import Union


class PotentialSecret:
    """This custom data type represents a string found, matching the
    plugin rules defined in SecretsCollection, that has the potential
    to be a secret that we actually care about.

    "Potential" is the operative word here, because of the nature of
    false positives.

    We use this custom class so that we can more easily generate data
    structures and do object-based comparisons with other PotentialSecrets,
    without actually knowing what the secret is.
    """

    def __init__(
        self,
        typ,
        filename,
        secret,
        lineno=0,
        is_secret=None,
        output_raw=False,
        is_verified=False,
        verified_result=None,
    ):
        """
        :type typ: str
        :param typ: human-readable secret type, defined by the plugin
                    that generated this PotentialSecret.
                    e.g. "High Entropy String"

        :type filename: str
        :param filename: name of file that this secret was found

        :type secret: str
        :param secret: the actual secret identified

        :type lineno: int
        :param lineno: location of secret, within filename.
                       Merely used as a reference for easy triage.

        :type is_secret: bool|None
        :param is_secret: whether or not the secret is a true- or false- positive

        :type is_verified: bool
        :param is_verified: whether the secret has been externally verified

        :type output_raw: bool|None
        :param output_raw: whether or not to output the raw, unhashed secret
        """
        self.type = typ
        self.filename = filename
        self.lineno = lineno
        self.secret_hash = self.hash_secret(secret)
        self.secret = secret
        self.is_secret = is_secret
        self.is_verified = is_verified
        self.verified_result = verified_result
        self.other_factors = {}

        # NOTE: Originally, we never wanted to keep the secret value in memory,
        #       after finding it in the codebase. However, to support verifiable
        #       secrets (and avoid the pain of re-scanning again), we need to
        #       keep the plaintext in memory as such.
        #
        #       This value should never appear in the baseline though, seeing that
        #       we don't want to create a file that contains all plaintext secrets
        #       in the repository.
        self.secret_value = secret
        self.output_raw = output_raw

        # If two PotentialSecrets have the same values for these fields,
        # they are considered equal. Note that line numbers aren't included
        # in this, because line numbers are subject to change.
        self.fields_to_compare = ['filename', 'secret_hash', 'type']

    def set_secret(self, secret):
        self.secret_hash = self.hash_secret(secret)
        self.secret_value = secret

    @staticmethod
    def hash_secret(secret):
        """This offers a way to coherently test this class,
        without mocking self.secret_hash.

        :type secret: string
        :rtype: string
        """
        return hashlib.sha1(secret.encode('utf-8')).hexdigest()

    @classmethod
    def load_secret_from_dict(cls, data: Dict[str, Union[str, int, bool]]) -> 'PotentialSecret':
        """Custom JSON decoder"""
        kwargs: Dict[str, Any] = {
            'typ': str(data['type']),
            'filename': str(data['filename']),
            'secret': 'will be replaced',
        }

        print('data before', data)
        # Optional parameters
        for parameter in {
            'lineno',
            'is_secret',
            'is_verified',
        }:
            if parameter in data:
                kwargs[parameter] = data[parameter]

        print('kwargs is', kwargs)
        print('data after', data)
        print('cls is', cls)
        output = cls(**kwargs)
        output.secret_value = None
        output.secret_hash = str(data['hashed_secret'])
        print('output is', output)

        return output

    def json(self):
        """Custom JSON encoder"""
        attributes = {
            'type': self.type,
            'filename': self.filename,
            'line_number': self.lineno,
            'hashed_secret': self.secret_hash,
            'is_verified': self.is_verified,
            'verified_result': self.verified_result,
        }

        if self.output_raw:
            attributes['secret'] = self.secret

        if self.is_secret is not None:
            attributes['is_secret'] = self.is_secret

        if self.other_factors:
            attributes['other_factors'] = self.other_factors

        return attributes

    def __eq__(self, other):
        return all(
            getattr(self, field) == getattr(other, field)
            for field in self.fields_to_compare
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(
            tuple(
                getattr(self, x)
                for x in self.fields_to_compare
            ),
        )

    def __str__(self):  # pragma: no cover
        return (
            'Secret Type: %s\n'
            'Location:    %s:%d\n'
        ) % (
            self.type,
            self.filename, self.lineno,
        )
