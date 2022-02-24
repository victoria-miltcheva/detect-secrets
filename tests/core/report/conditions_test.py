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
from testing.mocks import mock_printer as mock_printer_base


@pytest.fixture
def mock_printer():
    with mock_printer_base(audit) as shim:
        yield shim


class TestReportConditions:
    @contextmanager
    def mock_env(self, user_inputs=None, baseline=None):
        if baseline is None:
            baseline = self.baseline

        if not user_inputs:
            user_inputs = []

        with mock.patch.object(
            # We mock this, so we don't need to do any file I/O.
            audit,
            '_get_baseline_from_file',
            return_value=baseline,
        ), mock.patch.object(
            # We mock this because we don't really care about clearing
            # screens for test cases.
            audit,
            '_clear_screen',
        ), mock.patch.object(
            # Tests for this fall under a different test suite.
            audit,
            '_print_context',
        ), mock.patch.object(
            # We mock this so we don't modify the baseline.
            audit,
            '_remove_nonexistent_files_from_baseline',
            return_value=False,
        ), mock.patch.object(
            # We mock this so we don't need to do any file I/O.
            audit,
            'write_baseline_to_file',
        ) as m:
            yield m

    @property
    def baseline(self):
        return {
            'generated_at': 'some timestamp',
            'plugins_used': [
                {
                    'name': 'TestPlugin',
                },
            ],
            'results': {
                'filenameA': [
                    {
                        'hashed_secret': 'a',
                        'line_number': 122,
                        'type': 'Test Type',
                    },
                    {
                        'hashed_secret': 'b',
                        'line_number': 123,
                        'type': 'Test Type',
                    },
                ],
                'filenameB': [
                    {
                        'hashed_secret': 'c',
                        'line_number': 123,
                        'type': 'Test Type',
                    },
                ],
            },
        }

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
