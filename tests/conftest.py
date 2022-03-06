from typing import List

import pytest

from detect_secrets.core.report.constants import ReportedSecret
from detect_secrets.core.report.constants import ReportSecretType
from testing.baseline import baseline_filename

# https://docs.pytest.org/en/6.2.x/fixture.html#scope-sharing-fixtures-across-classes-modules-packages-or-session


@pytest.fixture
def live_secrets_fixture():
    live_secrets: List[ReportedSecret] = [
        {
            'failed_condition': ReportSecretType.LIVE.value,
            'filename': baseline_filename,
            'line': 90,
            'type': 'Private key',
        },
    ]
    return live_secrets


@pytest.fixture
def unaudited_secrets_fixture():
    unaudited_secrets: List[ReportedSecret] = [
        {
            'failed_condition': ReportSecretType.UNAUDITED.value,
            'filename': baseline_filename,
            'line': 120,
            'type': 'Hex High Entropy String',
        },
    ]
    return unaudited_secrets


@pytest.fixture
def audited_real_secrets_fixture():
    audited_real_secrets: List[ReportedSecret] = [
        {
            'failed_condition': ReportSecretType.AUDITED_REAL.value,
            'filename': baseline_filename,
            'line': 60,
            'type': 'Hex High Entropy String',
        },
    ]

    return audited_real_secrets
