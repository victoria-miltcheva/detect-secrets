from contextlib import contextmanager
from copy import deepcopy

import mock
import numpy
import pytest

from detect_secrets.core import audit
from detect_secrets.core.report.conditions import fail_on_audited_real
from detect_secrets.core.report.conditions import fail_on_live
from detect_secrets.core.report.conditions import fail_on_unaudited
from detect_secrets.core.report.constants import ReportExitCode
from detect_secrets.core.report.constants import ReportSecretType
from testing.fixtures import baseline
from testing.mocks import mock_printer as mock_printer_base


@pytest.fixture
def mock_printer():
    with mock_printer_base(audit) as shim:
        yield shim


class TestReportConditions:
    @contextmanager
    def mock_env(self, baseline=None):
        if baseline is None:
            baseline = self.baseline

        with mock.patch.object(
            # We mock this, so we don't need to do any file I/O.
            audit,
            '_get_baseline_from_file',
            return_value=baseline,
        ) as m:
            yield m

    @property
    def baseline(self):
        return baseline

    def test_unaudited_pass_case(self):
        modified_baseline = deepcopy(self.baseline)
        modified_baseline['results']['filenameA'][0]['is_secret'] = False
        modified_baseline['results']['filenameA'][1]['is_secret'] = False
        modified_baseline['results']['filenameB'][0]['is_secret'] = False

        with self.mock_env(baseline=modified_baseline):
            (return_code, secrets) = fail_on_unaudited('will_be_mocked')

        assert return_code == ReportExitCode.PASS.value
        assert len(secrets) == 0

    def test_unaudited_fail_case(self, mock_printer):
        modified_baseline = deepcopy(self.baseline)
        modified_baseline['results']['filenameA'][0]['is_secret'] = None
        modified_baseline['results']['filenameA'][1]['is_secret'] = None
        modified_baseline['results']['filenameB'][0]['is_secret'] = None

        with self.mock_env(baseline=modified_baseline):
            (return_code, secrets) = fail_on_unaudited('will_be_mocked')

        expected_secrets = [
            {
                'failed_condition': ReportSecretType.UNAUDITED.value,
                'filename': 'filenameA',
                'line': modified_baseline['results']['filenameA'][0]['line_number'],
                'type': 'Test Type',
            },
            {
                'failed_condition': ReportSecretType.UNAUDITED.value,
                'filename': 'filenameA',
                'line': modified_baseline['results']['filenameA'][1]['line_number'],
                'type': 'Test Type',
            },
            {
                'failed_condition': ReportSecretType.UNAUDITED.value,
                'filename': 'filenameB',
                'line': modified_baseline['results']['filenameB'][0]['line_number'],
                'type': 'Test Type',
            },
        ]

        assert return_code == ReportExitCode.FAIL.value
        assert len(secrets) == len(expected_secrets)
        assert (numpy.array(expected_secrets) == numpy.array(secrets)).all()

    def test_live_pass_case(self):
        modified_baseline = deepcopy(self.baseline)
        modified_baseline['results']['filenameA'][0]['is_verified'] = False
        modified_baseline['results']['filenameA'][1]['is_verified'] = False
        modified_baseline['results']['filenameB'][0]['is_verified'] = False

        with self.mock_env(baseline=modified_baseline):
            (return_code, secrets) = fail_on_live('will_be_mocked')

        assert return_code == ReportExitCode.PASS.value
        assert len(secrets) == 0

    def test_live_fail_case(self):
        modified_baseline = deepcopy(self.baseline)
        modified_baseline['results']['filenameA'][0]['is_verified'] = True
        modified_baseline['results']['filenameA'][1]['is_verified'] = True
        modified_baseline['results']['filenameB'][0]['is_verified'] = True

        expected_secrets = [
            {
                'failed_condition': ReportSecretType.LIVE.value,
                'filename': 'filenameA',
                'line': modified_baseline['results']['filenameA'][0]['line_number'],
                'type': 'Test Type',
            },
            {
                'failed_condition': ReportSecretType.LIVE.value,
                'filename': 'filenameA',
                'line': modified_baseline['results']['filenameA'][1]['line_number'],
                'type': 'Test Type',
            },
            {
                'failed_condition': ReportSecretType.LIVE.value,
                'filename': 'filenameB',
                'line': modified_baseline['results']['filenameB'][0]['line_number'],
                'type': 'Test Type',
            },
        ]

        with self.mock_env(baseline=modified_baseline):
            (return_code, secrets) = fail_on_live('will_be_mocked')

        assert return_code == ReportExitCode.FAIL.value
        assert len(secrets) == len(expected_secrets)
        assert (numpy.array(expected_secrets) == numpy.array(secrets)).all()

    def test_audited_real_pass_case(self):
        modified_baseline = deepcopy(self.baseline)
        modified_baseline['results']['filenameA'][0]['is_secret'] = False
        modified_baseline['results']['filenameA'][1]['is_secret'] = False
        modified_baseline['results']['filenameB'][0]['is_secret'] = False

        with self.mock_env(baseline=modified_baseline):
            (return_code, secrets) = fail_on_audited_real('will_be_mocked')

        assert return_code == ReportExitCode.PASS.value
        assert len(secrets) == 0

    def test_audited_real_fail_case(self):
        modified_baseline = deepcopy(self.baseline)
        modified_baseline['results']['filenameA'][0]['is_secret'] = True
        modified_baseline['results']['filenameA'][1]['is_secret'] = True
        modified_baseline['results']['filenameB'][0]['is_secret'] = True

        expected_secrets = [
            {
                'failed_condition': ReportSecretType.AUDITED_REAL.value,
                'filename': 'filenameA',
                'line': modified_baseline['results']['filenameA'][0]['line_number'],
                'type': 'Test Type',
            },
            {
                'failed_condition': ReportSecretType.AUDITED_REAL.value,
                'filename': 'filenameA',
                'line': modified_baseline['results']['filenameA'][1]['line_number'],
                'type': 'Test Type',
            },
            {
                'failed_condition': ReportSecretType.AUDITED_REAL.value,
                'filename': 'filenameB',
                'line': modified_baseline['results']['filenameB'][0]['line_number'],
                'type': 'Test Type',
            },
        ]

        print('expected_secrets', expected_secrets)

        with self.mock_env(baseline=modified_baseline):
            (return_code, secrets) = fail_on_audited_real('will_be_mocked')

        assert return_code == ReportExitCode.FAIL.value
        assert len(secrets) == len(expected_secrets)
        assert (numpy.array(expected_secrets) == numpy.array(secrets)).all()
