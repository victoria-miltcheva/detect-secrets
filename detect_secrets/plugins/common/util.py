import os
import sys
from abc import abstractproperty
from functools import lru_cache
from importlib import import_module

from detect_secrets.plugins.base import BasePlugin
from detect_secrets.util.git import get_root_directory


@lru_cache(maxsize=1)
def get_mapping_from_secret_type_to_class_name(plugin_filenames=None):
    """Returns secret_type => plugin classname"""
    return {
        plugin.secret_type: name
        for name, plugin in import_plugins(plugin_filenames=plugin_filenames).items()
    }


@lru_cache(maxsize=1)
def import_plugins(plugin_filenames=None):
    """
    :type plugin_filenames: tuple
    :param plugin_filenames: the plugin filenames.

    :rtype: Dict[str, Type[TypeVar('Plugin', bound=BasePlugin)]]
    """
    modules = []
    for root, _, files in os.walk(
        os.path.join(get_root_directory(), 'detect_secrets/plugins'),
    ):
        for filename in files:
            if not filename.startswith('_'):
                modules.append(os.path.splitext(filename)[0])

        # Only want to import top level files
        break

    plugins = {}
    for module_name in modules:
        # If plugin_filenames is None, all of the plugins will get imported.
        # Normal runs of this will have plugin_filenames set.
        # plugin_filenames will be None if we are testing a method and don't pass it in.
        if plugin_filenames is None or module_name in plugin_filenames:
            try:
                module = import_module('detect_secrets.plugins.{}'.format(module_name))
            except ModuleNotFoundError as err:  # pragma: no cover
                if hasattr(err, 'msg'):
                    message = err.msg
                if "No module named 'ibm_db'" not in message:
                    raise err
                else:
                    yellow = '\033[93m'
                    end_yellow = '\033[0m'
                    print(
                        yellow,
                        'Warning: ibm_db is not installed, the DB2 plugin will not run.\n',
                        'To enable the optional DB2 plugin, install ibm_db with:\n',
                        'pip install ibm_db\n',
                        'and run detect secrets with',
                        'detect-secrets scan --update .secrets.baseline --db2-scan',
                        end_yellow,
                        file=sys.stderr,
                        flush=True,
                    )
                    continue

            for name in filter(lambda x: not x.startswith('_'), dir(module)):
                plugin = getattr(module, name)
                try:
                    if not issubclass(plugin, BasePlugin):
                        continue
                except TypeError:
                    # Occurs when plugin is not a class type.
                    continue

                # Use this as a heuristic to determine abstract classes
                if isinstance(plugin.secret_type, abstractproperty):
                    continue

                plugins[name] = plugin

    return plugins
