import os
import urlparse

import jinja2
import six

from pypo4sel import PageElementsContainer
from pypo4sel.core import log2l


class Config(dict):
    """Dictionary like helper class for maintaining test data configurations
    per environment.
The :class:`pypo4sel.base.configuration.Config` object is aware of the environment
and will return the config variable from that environment or from the `default` key.
Values in the config file can use :class:`jinja2.Template` templates to access
either values from itself, environment variables or a select specific to run
variables: ``run_config.environment``, ``run_config.browser`` and ``run_config.remote``
Example config structure (which uses an environment variable ``$PATH``).

.. code-block:: python
    config = {
        {
            'default': {
                'path':"{{PATH}}",
                'browsers': {
                    'chrome': {'driver_path': '/usr/bin/chromedriver'}
                },
                'browser': '{{ common.browsers[run_config.browser]|default({}) }}',
                'login_url': '{{url}/login}'
            },
            'production': {'url':'http://prod.com'},
            'development': {
                'url':'http://dev.com',
                'browser': {{browsers.chrome}}
            }
        }
    }

When accessing config, due to the default:
* ``config['path']`` will always return the value of the environment
   variable `PATH`,
if environment is ``production``:
* ``config['browser']`` will chrome if run_config.browser == chrome, and empty dict in all other cases
* ``config['login_url']`` will return ``http://prod.com/login``
if environment is ``development``:
* ``self.config['login_url']`` will return ``http://dev.com/development/login``
* ``config['browser']`` will always chrome
    """

    # noinspection PyTypeChecker
    def __init__(self, dct, run_config=None):
        if not run_config:
            run_config = {'environment': 'development', 'browser': 'firefox'}
        self._run_config = run_config
        dict.__init__(self, dct)
        self._env_context = dict.setdefault(self, self._run_config["environment"], {})
        self._common_context = dict.setdefault(self, "common", {})

        self._context = dict(self)
        self._context.update(os.environ)
        self._context.update({'run_config': self._run_config})
        self._context.update(self._common_context)
        self._context.update(self._env_context)

    def __getitem__(self, key):
        def __render(_item, _context):
            if isinstance(_item, six.string_types):
                template = jinja2.Template(_item)
                rendered = template.render(_context)
                if rendered != _item:
                    return __render(rendered, _context)
                else:
                    return rendered
            else:
                return item

        try:
            item = self._env_context[key]
        except KeyError:
            item = self._common_context[key]

        return __render(item, self._context)


class ContextManager(object):
    """
    any global options
    default_environment - common for all environments and default options
    environment - specific for environment option, overridden common options
        context - specific for context option, overridden environment options



    - change context: Context.set
    """
    base_url = ""
    driver = None

    def __init__(self):
        self.config = Config(
            {'common': {'browsers': {}, 'browser': '{{ common.browsers[run_config.browser]|default({}) }}'}})
        self.driver = (self.config["run_config"]["browser"], self.config["browser"])


class Page(PageElementsContainer):
    @property
    def driver(self):
        return ContextManager.driver

    url = "/"

    def open(self, parameters=()):
        url = urlparse.urljoin(ContextManager.base_url, self.url) % parameters
        with log2l.step("get {} at {}".format(self.__class__.__name__, url)):
            self.driver.get(url)
