# import codecs
# import io
# import json
# import os
# import sys
# from builtins import input
# from collections import defaultdict
# from copy import deepcopy
# from functools import lru_cache
# from enum import Enum
# from typing import Any
# from typing import Callable
# from typing import Dict
# from typing import List
# from typing import Tuple
# from ..plugins.common import initialize
# from ..plugins.common.util import get_mapping_from_secret_type_to_class_name
# from ..util import get_git_remotes
# from ..util import get_git_sha
# from ..constants import VerifiedResult
# from .baseline import merge_results
# from .bidirectional_iterator import BidirectionalIterator
# from .code_snippet import CodeSnippetHighlighter
# from .color import AnsiColor
# from .color import colorize
# from .common import write_baseline_to_file
# class SecretNotFoundOnSpecifiedLineError(Exception):
#     def __init__(self, line):
#         super(SecretNotFoundOnSpecifiedLineError, self).__init__(
#             'ERROR: Secret not found on line {}!\n'.format(line)
#             + 'Try recreating your baseline to fix this issue.',
#         )
# class RedundantComparisonError(Exception):
#     pass
# AUDIT_RESULT_TO_STRING = {
#     True: 'true-positives',
#     False: 'false-positives',
#     None: 'unknowns',
# }
# EMPTY_PLUGIN_AUDIT_RESULT = {
#     'results': {
#         'true-positives': defaultdict(list),
#         'false-positives': defaultdict(list),
#         'unknowns': defaultdict(list),
#     },
#     'config': {},
# }
# EMPTY_STATS_RESULT = {
#     'signal': 0,
#     'true-positives': {
#         'count': 0,
#         'files': defaultdict(int),
#     },
#     'false-positives': {
#         'count': 0,
#         'files': defaultdict(int),
#     },
#     'unknowns': {
#         'count': 0,
#         'files': defaultdict(int),
#     },
# }
# def audit_baseline(baseline_filename):
#     original_baseline = _get_baseline_from_file(baseline_filename)
#     if not original_baseline:
#         return
#     files_removed = _remove_nonexistent_files_from_baseline(original_baseline)
#     all_secrets = list(_secret_generator(original_baseline))
#     secrets_with_choices = [
#         (filename, secret) for filename, secret in all_secrets
#         if 'is_secret' not in secret
#     ]
#     total_choices = len(secrets_with_choices)
#     secret_iterator = BidirectionalIterator(secrets_with_choices)
#     if sys.platform.lower() == 'win32':
#         # required on Windows to enable ANSI escape codes to print correctly!
#         # noqa: E501 See: https://stackoverflow.com/questions/287871/how-to-print-colored-text-in-terminal-in-python
#         os.system('')
#     current_secret_index = 0
#     for filename, secret in secret_iterator:
#         _clear_screen()
#         current_secret_index += 1
#         try:
#             _print_context(
#                 filename,
#                 secret,
#                 current_secret_index,
#                 total_choices,
#                 original_baseline['plugins_used'],
#             )
#             decision = _get_user_decision(can_step_back=secret_iterator.can_step_back())
#         except SecretNotFoundOnSpecifiedLineError:
#             decision = _get_user_decision(
#                 prompt_secret_decision=False,
#                 can_step_back=secret_iterator.can_step_back(),
#             )
#         if decision == 'q':
#             print('Quitting...')
#             break
#         if decision == 'b':
#             current_secret_index -= 2
#             secret_iterator.step_back_on_next_iteration()
#         _handle_user_decision(decision, secret)
#     if current_secret_index == 0 and not files_removed:
#         print('Nothing to audit!')
#         return
#     print('Saving progress...')
#     results = defaultdict(list)
#     for filename, secret in all_secrets:
#         results[filename].append(secret)
#     original_baseline['results'] = merge_results(
#         original_baseline['results'],
#         dict(results),
#     )
#     write_baseline_to_file(
#         filename=baseline_filename,
#         data=original_baseline,
#     )
# def compare_baselines(old_baseline_filename, new_baseline_filename):
#     """
#     This function enables developers to more easily configure plugin
#     settings, by comparing two generated baselines and highlighting
#     their differences.
#     For effective use, a few assumptions are made:
#         1. Baselines are sorted by (filename, line_number, hash).
#            This allows for a deterministic order, when doing a side-by-side
#            comparison.
#         2. Baselines are generated for the same codebase snapshot.
#            This means that we won't have cases where secrets are moved around;
#            only added or removed.
#     NOTE: We don't want to do a version check, because we want to be able to
#     use this functionality across versions (to see how the new version fares
#     compared to the old one).
#     """
#     if old_baseline_filename == new_baseline_filename:
#         raise RedundantComparisonError
#     old_baseline = _get_baseline_from_file(old_baseline_filename)
#     new_baseline = _get_baseline_from_file(new_baseline_filename)
#     _remove_nonexistent_files_from_baseline(old_baseline)
#     _remove_nonexistent_files_from_baseline(new_baseline)
#     # We aggregate the secrets first, so that we can display a total count.
#     secrets_to_compare = _get_secrets_to_compare(old_baseline, new_baseline)
#     total_reviews = len(secrets_to_compare)
#     current_index = 0
#     secret_iterator = BidirectionalIterator(secrets_to_compare)
#     for filename, secret, is_removed in secret_iterator:
#         _clear_screen()
#         current_index += 1
#         header = '{}      {}'
#         if is_removed:
#             plugins_used = old_baseline['plugins_used']
#             header = header.format(
#                 colorize('Status:', AnsiColor.BOLD),
#                 '>> {} <<'.format(
#                     colorize('REMOVED', AnsiColor.RED),
#                 ),
#             )
#         else:
#             plugins_used = new_baseline['plugins_used']
#             header = header.format(
#                 colorize('Status:', AnsiColor.BOLD),
#                 '>> {} <<'.format(
#                     colorize('ADDED', AnsiColor.LIGHT_GREEN),
#                 ),
#             )
#         try:
#             _print_context(
#                 filename,
#                 secret,
#                 current_index,
#                 total_reviews,
#                 plugins_used,
#                 additional_header_lines=header,
#                 force=is_removed,
#             )
#             decision = _get_user_decision(
#                 can_step_back=secret_iterator.can_step_back(),
#                 prompt_secret_decision=False,
#             )
#         except SecretNotFoundOnSpecifiedLineError:
#             decision = _get_user_decision(prompt_secret_decision=False)
#         if decision == 'q':
#             print('Quitting...')
#             break
#         if decision == 'b':  # pragma: no cover
#             current_index -= 2
#             secret_iterator.step_back_on_next_iteration()
# def determine_audit_results(baseline, baseline_path):
#     """
#     Given a baseline which has been audited, returns
#     a dictionary describing the results of each plugin in the following form:
#     {
#         "plugins": {
#             "plugin_name1": {
#                 "results": {
#                     "true-positives": [
#                         list of {
#                             filename: {
#                                 'line': '...',
#                                 'plaintext':'...',
#                             }
#                         } for secrets with `is_secret: true` caught by this plugin],
#                     "false-positives": [
#                         list of {
#                             filename: {
#                                 'line': '...',
#                                 'plaintext':'...',
#                             }
#                         } for secrets with `is_secret: false` caught by this plugin],
#                     "unknowns": [
#                         list of {
#                             filename: {
#                                 'line': '...',
#                                 'plaintext':'...',
#                             }
#                         } for secrets with no `is_secret` entry caught by this plugin]
#                 },
#                 "config": {configuration used for the plugin}
#             },
#             ...
#         },
#         "repo_info": {
#             "remote": "remote url",
#             "sha": "sha of repo checkout"
#         },
#     }
#     """
#     all_secrets = _secret_generator(baseline)
#     audit_results = {
#         'plugins': defaultdict(lambda: deepcopy(EMPTY_PLUGIN_AUDIT_RESULT)),
#         'stats': deepcopy(EMPTY_STATS_RESULT),
#     }
#     secret_type_to_plugin_name = get_mapping_from_secret_type_to_class_name()
#     total = 0
#     for filename, secret in all_secrets:
#         file_contents = _open_file_with_cache(filename)
#         secret_info = {}
#         secret_info['line'] = _get_file_line(filename, secret['line_number'])
#         try:
#             secret_info['plaintext'] = get_raw_secret_value(
#                 secret=secret,
#                 plugin_settings=baseline['plugins_used'],
#                 file_handle=io.StringIO(file_contents),
#                 filename=filename,
#             )
#         except SecretNotFoundOnSpecifiedLineError:
#             secret_info['plaintext'] = None
#         plugin_name = secret_type_to_plugin_name[secret['type']]
#         audit_result = AUDIT_RESULT_TO_STRING[secret.get('is_secret')]
#         audit_results['plugins'][plugin_name]['results'][audit_result][filename].append(secret_info)
#         audit_results['stats'][audit_result]['count'] += 1
#         audit_results['stats'][audit_result]['files'][filename] += 1
#         total += 1
#     if total > 0:
#         audit_results['stats']['signal'] = str(
#             (
#                 float(audit_results['stats']['true-positives']['count'])
#                 /
#                 total
#             ) * 100,
#         )[:4] + '%'
#     for plugin_config in baseline['plugins_used']:
#         plugin_name = plugin_config['name']
#         if plugin_name not in audit_results['plugins']:
#             continue
#         audit_results['plugins'][plugin_name]['config'].update(plugin_config)
#     git_repo_path = os.path.dirname(os.path.abspath(baseline_path))
#     git_sha = get_git_sha(git_repo_path)
#     git_remotes = get_git_remotes(git_repo_path)
#     if git_sha and git_remotes:
#         audit_results['repo_info'] = {
#             'remote': git_remotes[0],
#             'sha': git_sha,
#         }
#     return audit_results
# def print_audit_results(baseline_filename):
#     baseline = _get_baseline_from_file(baseline_filename)
#     if not baseline:
#         print('Failed to retrieve baseline from {filename}'.format(filename=baseline_filename))
#         return
#     print(
#         json.dumps(
#             determine_audit_results(
#                 baseline,
#                 baseline_filename,
#             ),
#             indent=2,
#             sort_keys=True,
#         ),
#     )
# def _get_baseline_from_file(filename):  # pragma: no cover
#     try:
#         with open(filename) as f:
#             return json.loads(f.read())
#     except (IOError, json.decoder.JSONDecodeError):
#         print('Not a valid baseline file!', file=sys.stderr)
#         return
# def _remove_nonexistent_files_from_baseline(baseline):
#     files_removed = False
#     for filename in baseline['results'].copy():
#         if not os.path.exists(filename):
#             del baseline['results'][filename]
#             files_removed = True
#     return files_removed
# def _secret_generator(baseline):
#     """Generates secrets to audit, from the baseline"""
#     for filename, secrets in baseline['results'].items():
#         for secret in secrets:
#             yield filename, secret
# def _get_secrets_to_compare(old_baseline, new_baseline):
#     """
#     :rtype: list(tuple)
#     :param: tuple is in the following format:
#         filename: str; filename where identified secret is found
#         secret: dict; PotentialSecret json representation
#         is_secret_removed: bool; has the secret been removed from the
#             new baseline?
#     """
#     def _check_string(a, b):
#         if a == b:
#             return 0
#         if a < b:
#             return -1
#         return 1
#     def _check_secret(a, b):
#         if a == b:
#             return 0
#         if a['line_number'] < b['line_number']:
#             return -1
#         elif a['line_number'] > b['line_number']:
#             return 1
#         return _check_string(a['hashed_secret'], b['hashed_secret'])
#     secrets_to_compare = []
#     for old_filename, new_filename in _comparison_generator(
#         sorted(old_baseline['results'].keys()),
#         sorted(new_baseline['results'].keys()),
#         compare_fn=_check_string,
#     ):
#         if not new_filename:
#             secrets_to_compare += list(
#                 map(
#                     lambda x: (old_filename, x, True),
#                     old_baseline['results'][old_filename],
#                 ),
#             )
#             continue
#         elif not old_filename:
#             secrets_to_compare += list(
#                 map(
#                     lambda x: (new_filename, x, False),
#                     new_baseline['results'][new_filename],
#                 ),
#             )
#             continue
#         for old_secret, new_secret in _comparison_generator(
#             old_baseline['results'][old_filename],
#             new_baseline['results'][new_filename],
#             compare_fn=_check_secret,
#         ):
#             if old_secret == new_secret:
#                 # If they are the same, no point flagging it.
#                 continue
#             if old_secret:
#                 secrets_to_compare.append(
#                     (old_filename, old_secret, True),
#                 )
#             else:
#                 secrets_to_compare.append(
#                     (new_filename, new_secret, False),
#                 )
#     return secrets_to_compare
# def _comparison_generator(old_list, new_list, compare_fn):
#     """
#     :type old_list: sorted list
#     :type new_list: sorted list
#     :type compare_fn: function
#     :param compare_fn:
#         takes two arguments, A and B
#         returns 0 if equal
#         returns -1 if A is less than B
#         else returns 1
#     """
#     old_index = 0
#     new_index = 0
#     while old_index < len(old_list) and new_index < len(new_list):
#         old_value = old_list[old_index]
#         new_value = new_list[new_index]
#         status = compare_fn(old_value, new_value)
#         if status == 0:
#             yield (old_value, new_value)
#             old_index += 1
#             new_index += 1
#         elif status == -1:
#             yield (old_value, None)
#             old_index += 1
#         else:
#             yield (None, new_value)
#             new_index += 1
#     # Catch leftovers. Only one of these while statements should run.
#     while old_index < len(old_list):
#         yield (old_list[old_index], None)
#         old_index += 1
#     while new_index < len(new_list):
#         yield (None, new_list[new_index])
#         new_index += 1
# def _clear_screen():  # pragma: no cover
#     print('\033[2J\033[H', end='')  # ANSI escapes for: clear screen, move cursor to home
# def _print_context(  # pragma: no cover
#     filename,
#     secret,
#     count,
#     total,
#     plugin_settings,
#     additional_header_lines=None,
#     force=False,
# ):
#     """
#     :type filename: str
#     :param filename: the file currently scanned.
#     :type secret: dict, in PotentialSecret.json() format
#     :param secret: the secret, represented in the baseline file.
#     :type count: int
#     :param count: current count of secrets scanned so far
#     :type total: int
#     :param total: total number of secrets in baseline
#     :type plugin_settings: list
#     :param plugin_settings: plugins used to create baseline.
#     :type additional_header_lines: str
#     :param additional_header_lines: any additional lines to add to the
#         header of the interactive audit display.
#     :type force: bool
#     :param force: if True, will print the lines of code even if it doesn't
#         find the secret expected
#     :raises: SecretNotFoundOnSpecifiedLineError
#     """
#     print(
#         '{} {} {} {}\n{} {}\n{} {}'.format(
#             colorize('Secret:     ', AnsiColor.BOLD),
#             colorize(str(count), AnsiColor.PURPLE),
#             colorize('of', AnsiColor.BOLD),
#             colorize(str(total), AnsiColor.PURPLE),
#             colorize('Filename:   ', AnsiColor.BOLD),
#             colorize(filename, AnsiColor.PURPLE),
#             colorize('Secret Type:', AnsiColor.BOLD),
#             colorize(secret['type'], AnsiColor.PURPLE),
#         ),
#     )
#     if additional_header_lines:
#         print(additional_header_lines)
#     print('-' * 10)
#     error_obj = None
#     try:
#         secret_with_context = _get_secret_with_context(
#             filename,
#             secret,
#             plugin_settings,
#             force=force,
#         )
#         print(secret_with_context)  # lgtm [py/clear-text-logging-sensitive-data]
#     except SecretNotFoundOnSpecifiedLineError as e:
#         error_obj = e
#         print(e)
#     print('-' * 10)
#     if error_obj:
#         raise error_obj
# def _get_user_decision(prompt_secret_decision=True, can_step_back=False):
#     """
#     :type prompt_secret_decision: bool
#     :param prompt_secret_decision: if False, won't ask to label secret.
#     """
#     allowable_user_input = ['s', 'q']
#     if prompt_secret_decision:
#         allowable_user_input.extend(['y', 'n'])
#     if can_step_back:
#         allowable_user_input.append('b')
#     user_input = None
#     while user_input not in allowable_user_input:
#         if user_input:
#             print('Invalid input.')
#         if 'y' in allowable_user_input:
#             user_input_string = 'Is this a valid secret? i.e. not a false-positive (y)es, (n)o, '
#         else:
#             user_input_string = 'What would you like to do? '
#         if 'b' in allowable_user_input:
#             user_input_string += '(b)ack, '
#         user_input_string += '(s)kip, (q)uit: '
#         user_input = input(user_input_string)
#         if user_input:
#             user_input = user_input[0].lower()
#     return user_input
# def _handle_user_decision(decision, secret):
#     if decision == 'y':
#         secret['is_secret'] = True
#     elif decision == 'n':
#         secret['is_secret'] = False
#     elif decision == 's' and 'is_secret' in secret:
#         del secret['is_secret']
# @lru_cache(maxsize=1)
# def _open_file_with_cache(filename):
#     """
#     Reads the input file and returns the result as a string.
#     This caches opened files to ensure that the audit functionality
#     doesn't unnecessarily re-open the same file.
#     """
#     try:
#         with codecs.open(filename, encoding='utf-8') as f:
#             return f.read()
#     except (OSError, IOError):
#         return None
# def _get_file_line(filename, line_number):
#     """
#     Attempts to read a given line from the input file.
#     """
#     file_content = _open_file_with_cache(filename)
#     if not file_content:
#         return None
#     return file_content.splitlines()[line_number - 1]
# def _get_secret_with_context(
#     filename,
#     secret,
#     plugin_settings,
#     lines_of_context=5,
#     force=False,
# ):
#     """
#     Displays the secret, with surrounding lines of code for better context.
#     :type filename: str
#     :param filename: filename where secret resides in
#     :type secret: dict, PotentialSecret.json() format
#     :param secret: the secret listed in baseline
#     :type plugin_settings: list
#     :param plugin_settings: plugins used to create baseline.
#     :type lines_of_context: int
#     :param lines_of_context: number of lines displayed before and after
#         secret.
#     :type force: bool
#     :param force: if True, will print the lines of code even if it doesn't
#         find the secret expected
#     :raises: SecretNotFoundOnSpecifiedLineError
#     """
#     try:
#         file_content = _open_file_with_cache(filename)
#         if not file_content:
#             raise SecretNotFoundOnSpecifiedLineError(secret['line_number'])
#         file_lines = file_content.splitlines()
#         snippet = CodeSnippetHighlighter().get_code_snippet(
#             file_lines,
#             secret['line_number'],
#             lines_of_context=lines_of_context,
#         )
#         raw_secret_value = get_raw_secret_value(
#             secret,
#             plugin_settings,
#             io.StringIO(file_content),
#             filename,
#         )
#         try:
#             snippet.highlight_line(raw_secret_value)
#         except ValueError:
#             raise SecretNotFoundOnSpecifiedLineError(secret['line_number'])
#     except SecretNotFoundOnSpecifiedLineError:
#         if not force:
#             raise
#         snippet.target_line = colorize(
#             snippet.target_line,
#             AnsiColor.BOLD,
#         )
#     return snippet.add_line_numbers()
# def get_raw_secret_value(
#     secret,
#     plugin_settings,
#     file_handle,
#     filename,
#     plugin_filenames=None,
# ):
#     """
#     :type secret: dict
#     :param secret: see caller's docstring
#     :type plugin_settings: list
#     :param plugin_settings: see caller's docstring
#     :type file_handle: file object
#     :param file_handle: Open handle to file where the secret is
#     :type filename: str
#     :param filename: this is needed, because PotentialSecret uses this
#         as a means of comparing whether two secrets are equal.
#     :type plugin_filenames: tuple
#     :param plugin_filenames: the plugin filenames.
#     """
#     plugin = initialize.from_secret_type(
#         secret['type'],
#         plugin_settings,
#         plugin_filenames=plugin_filenames,
#     )
#     plugin_secrets = plugin.analyze(file_handle, filename)
#     # Return value of matching secret
#     for plugin_secret in plugin_secrets:
#         if plugin_secret.secret_hash == secret['hashed_secret']:
#             return plugin_secret.secret_value
#     raise SecretNotFoundOnSpecifiedLineError(secret['line_number'])
# def _get_raw_secrets_from_file(
#     secret: PotentialSecret,
#     line_getter_factory: Callable[[str], 'LineGetter'] = open_file,
# ) -> List[PotentialSecret]:
#     """
#     We're analyzing the contents straight from the baseline, and therefore, we don't know
#     the secret value (by design). However, we have secret hashes, filenames, and how we detected
#     it was a secret in the first place, so we can reverse-engineer it. This method searches all
#     the occurrences of one secret in one file using one plugin.
#     :raises: SecretNotFoundOnSpecifiedLineError
#     :raises: NoLineNumberError
#     """
#     plugin = cast(BasePlugin, plugins.initialize.from_secret_type(secret.type))
#     line_getter = line_getter_factory(secret.filename)
#     is_first_time_opening_file = not line_getter.has_cached_lines
#     all_secrets = []
#     while True:
#         if secret.line_number:
#             try:
#                 lines_to_scan = [line_getter.lines[secret.line_number - 1]]
#                 line_numbers = [secret.line_number - 1]
#             except IndexError:
#                 raise SecretNotFoundOnSpecifiedLineError(secret.line_number)
#         else:
#             lines_to_scan = line_getter.lines
#             line_numbers = list(range(len(lines_to_scan)))
#         for line_number, line in zip(line_numbers, lines_to_scan):
#             identified_secrets = call_function_with_arguments(
#                 plugin.analyze_line,
#                 filename=secret.filename,
#                 line=line,
#                 line_number=line_number + 1,
#                 # We enable eager search, because we *know* there's a secret here -- the baseline
#                 # flagged it after all.
#                 enable_eager_search=bool(secret.line_number),
#             )
#             for identified_secret in (identified_secrets or []):
#                 if identified_secret == secret:
#                     all_secrets.append(identified_secret)
#         if (
#             len(all_secrets) == 0 and
#             is_first_time_opening_file and
#             not line_getter.use_eager_transformers
#         ):
#             line_getter.use_eager_transformers = True
#         else:
#             return all_secrets
# @lru_cache(maxsize=1)
# def _open_file(filename: str) -> 'LineGetter':
#     return LineGetter(filename)
# class LineGetter:
#     """
#     The problem we try to address with this class is to cache the lines of a transformed file,
#     without knowing beforehand what type of transformation that file needs to undergo.
#     When we scan the file, we iterate through the transformed lines, in hopes of finding a
#     secret. If we do find something, we can break out of that iterator, and move on to the next
#     file.
#     However, when we audit the file, we *know* that we've found a secret in this location before
#     -- we just don't know what type of transformation the file had underwent to get there. As
#     such, we need to try all transformations until we find the secret that the scan told us about.
#     Once we find it, we should cache the results of that transformation so other audits of the
#     same file will be smoother.
#     We do this through a self-invalidating cache (self.lines), when we change the mode to using
#     eager transformers.
#     """
#     def __init__(self, filename: str) -> None:
#         self.filename = filename
#         self._lines: Optional[List[str]] = None
#         self._raw_lines: Optional[List[str]] = None
#         self._use_eager_transformers = False
#     @contextmanager
#     def open_file(self) -> Iterator[NamedIO]:
#         """This is split up into a different function, so it can be overridden if necessary."""
#         with open(self.filename) as f:
#             yield cast(NamedIO, f)
#     @property
#     def lines(self) -> List[str]:
#         if self._lines:
#             return self._lines
#         with self.open_file() as f:
#             lines = get_transformed_file(f, use_eager_transformers=self.use_eager_transformers)
#             self._lines = self.raw_lines if not lines else lines
#         return self._lines
#     @property
#     def raw_lines(self) -> List[str]:
#         if self._raw_lines:
#             return self._raw_lines
#         with self.open_file() as f:
#             self._raw_lines = [line.rstrip() for line in f.readlines()]
#         return self._raw_lines
#     @property
#     def has_cached_lines(self) -> bool:
#         return bool(self._lines)
#     @property
#     def use_eager_transformers(self) -> bool:
#         return self._use_eager_transformers
#     @use_eager_transformers.setter
#     def use_eager_transformers(self, status: bool) -> None:
#         if status == self.use_eager_transformers:
#             return
#         self._use_eager_transformers = status
#         self._lines = None              # invalidate cache
# class SecretClassToPrint(Enum):
#     REAL_SECRET = 1
#     FALSE_POSITIVE = 2
#     @staticmethod
#     def from_class(secret_class: VerifiedResult) -> 'SecretClassToPrint':
#         if secret_class in [VerifiedResult.UNVERIFIED, VerifiedResult.VERIFIED_TRUE]:
#             return SecretClassToPrint.REAL_SECRET
#         else:
#             return SecretClassToPrint.FALSE_POSITIVE
# def generate_report(
#     baseline_file: str,
#     class_to_print: SecretClassToPrint = None,
#     line_getter_factory: Callable[[str], 'LineGetter'] = _open_file,
# ) -> List[Dict[str, Any]]:
#     secrets: Dict[Tuple[str, str], Any] = {}
#     for filename, secret in _get_baseline_from_file(baseline_file):
#         verified_result = VerifiedResult.from_secret(secret)
#         if (
#             class_to_print is not None and
#             SecretClassToPrint.from_class(verified_result) != class_to_print
#         ):
#             continue
#         # Removal of the stored line number is required to force the complete file scanning to obtain all the secret occurrences. # noqa: E501
#         secret.line_number = 0
#         detections = _get_raw_secrets_from_file(secret)
#         line_getter = line_getter_factory(filename)
#         for detection in detections:
#             if (secret.secret_hash, filename) in secrets:
#                 secrets[(secret.secret_hash, filename)]['lines'][detection.line_number] = line_getter.lines[detection.line_number - 1]  # noqa: E501
#                 if secret.type not in secrets[(secret.secret_hash, filename)]['types']:
#                     secrets[(secret.secret_hash, filename)]['types'].append(secret.type)
#                 secrets[(secret.secret_hash, filename)]['category'] = get_prioritized_verified_result(  # noqa: E501
#                     verified_result,
#                     VerifiedResult[secrets[(secret.secret_hash, filename)]['category']],
#                 ).name
#             else:
#                 secrets[(secret.secret_hash, filename)] = {
#                     'secrets': detection.secret_value,
#                     'filename': filename,
#                     'lines': {
#                         detection.line_number: line_getter.lines[detection.line_number - 1],
#                     },
#                     'types': [
#                         secret.type,
#                     ],
#                     'category': verified_result.name,
#                 }
#     return list(secrets.values())
# def get_prioritized_verified_result(
#     result1: VerifiedResult,
#     result2: VerifiedResult,
# ) -> VerifiedResult:
#     if result1.value > result2.value:
#         return result1
#     else:
#         return result2
