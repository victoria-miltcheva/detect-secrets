from contextlib import contextmanager
from typing import List

import mock

from detect_secrets.core import audit
from detect_secrets.core.report.constants import ReportedSecret
from detect_secrets.core.report.constants import ReportSecretType
from detect_secrets.core.report.output import get_stats
from testing.fixtures import baseline


class TestReportOutput:
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

    def test_get_stats_no_failed_conditions(self):
        live_secrets = unaudited_secrets = audited_real_secrets = []
        baseline_filename = 'will_be_mocked'

        with self.mock_env():
            stats = get_stats(
                live_secrets,
                unaudited_secrets,
                audited_real_secrets,
                baseline_filename,
            )
            secrets = audit.get_secrets_list_from_file(baseline_filename)

        assert stats == {
            'reviewed': len(secrets),
            'live': len(live_secrets),
            'unaudited': len(unaudited_secrets),
            'audited_real': len(audited_real_secrets),
        }

    # TODO
    def test_get_stats_failed_conditions(self):
        baseline_filename: List[ReportedSecret] = 'will_be_mocked'
        live_secrets = [
            {
                'failed_condition': ReportSecretType.LIVE.value,
                'filename': baseline_filename,
                'line': 123,
                'type': 'Private key',
            },
        ]
        unaudited_secrets: List[ReportedSecret] = [
            {
                'failed_condition': ReportSecretType.UNAUDITED.value,
                'filename': baseline_filename,
                'line': 123,
                'type': 'Hex High Entropy String',
            },
        ]
        audited_real_secrets: List[ReportedSecret] = [
            {
                'failed_condition': ReportSecretType.AUDITED_REAL.value,
                'filename': baseline_filename,
                'line': 123,
                'type': 'Hex High Entropy String',
            },
        ]

        with self.mock_env():
            stats = get_stats(
                live_secrets,
                unaudited_secrets,
                audited_real_secrets,
                baseline_filename,
            )
            secrets = audit.get_secrets_list_from_file(baseline_filename)

        assert stats == {
            'reviewed': len(secrets),
            'live': len(live_secrets),
            'unaudited': len(unaudited_secrets),
            'audited_real': len(audited_real_secrets),
        }

    # TODO
    def test_print_stats_no_failed_conditions(self):
        assert True

    # TODO
    def test_print_stats_failed_conditions(self):
        assert True

    # TODO
    def test_print_report_table_no_failed_conditions(self):
        assert True

    # TODO
    def test_print_report_table_failed_conditions(self):
        assert True

    # TODO
    def test_print_json_report_no_failed_conditions(self):
        assert True

    # TODO
    def test_print_json_report_failed_conditions(self):
        assert True

    # TODO
    def test_print_summary_no_failed_conditions(self):
        assert True

    # TODO
    def test_print_summary_failed_conditions(self):
        assert True
