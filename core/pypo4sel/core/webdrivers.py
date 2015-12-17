import hashlib
import inspect

from selenium import webdriver

import common
import log2l


# TODO overwrite SwitchTo
# TODO move step text to resources
class WebDriverBase(common.FindOverride):
    implicitly_wait_timeout = 0
    script_wait_timeout = 0
    page_load_timeout = 0

    def implicitly_wait(self, time_to_wait):
        tm = float(time_to_wait)
        old = common.WAIT_ELEMENT_TIMEOUT
        common.WAIT_ELEMENT_TIMEOUT = tm
        self.implicitly_wait_timeout = tm
        return old

    def set_script_timeout(self, time_to_wait):
        # noinspection PyUnresolvedReferences
        super(WebDriverBase, self).set_script_timeout(time_to_wait)
        old = self.script_wait_timeout
        self.script_wait_timeout = time_to_wait
        return old

    def set_page_load_timeout(self, time_to_wait):
        # noinspection PyUnresolvedReferences
        super(WebDriverBase, self).set_page_load_timeout(time_to_wait)
        old = self.page_load_timeout
        self.page_load_timeout = time_to_wait
        return old

    @property
    def driver(self):
        return self

    @log2l.step
    def get(self, url):
        # noinspection PyUnresolvedReferences
        super(WebDriverBase, self).get(url)

    @log2l.step('Navigate one step backward in the browser history.')
    def back(self):
        # noinspection PyUnresolvedReferences
        super(WebDriverBase, self).back()

    @log2l.step('Navigate one step forward in the browser history.')
    def forward(self):
        # noinspection PyUnresolvedReferences
        super(WebDriverBase, self).forward()

    @log2l.step('Refresh the current page.')
    def refresh(self):
        # noinspection PyUnresolvedReferences
        super(WebDriverBase, self).refresh()

    def __hash__(self):
        # noinspection PyUnresolvedReferences
        return int(hashlib.md5(self.session_id).hexdigest(), 16)

    def __eq__(self, other):
        # noinspection PyUnresolvedReferences
        return other is not None and hasattr(other, "session_id") and self.session_id == other.session_id


class ChromeDriver(WebDriverBase, webdriver.Chrome):
    pass


class BlackBerryDriver(WebDriverBase, webdriver.BlackBerry):
    pass


class AndroidDriver(WebDriverBase, webdriver.Android):
    pass


class FirefoxDriver(WebDriverBase, webdriver.Firefox):
    pass


class SafariDriver(WebDriverBase, webdriver.Safari):
    pass


class RemoteDriver(WebDriverBase, webdriver.Remote):
    pass


class PhantomJSDriver(WebDriverBase, webdriver.PhantomJS):
    pass


class OperaDriver(WebDriverBase, webdriver.Opera):
    pass


class EdgeDriver(WebDriverBase, webdriver.Edge):
    pass


class IeDriver(WebDriverBase, webdriver.Ie):
    pass


BROWSER_MAPPING = {"remote": RemoteDriver,
                   "phantomjs": PhantomJSDriver,
                   "chrome": ChromeDriver,
                   "opera": OperaDriver,
                   "edge": EdgeDriver,
                   "blackberry": BlackBerryDriver,
                   "safari": SafariDriver,
                   "firefox": FirefoxDriver,
                   "android": AndroidDriver,
                   "ie": IeDriver}


def get_driver(browser='firefox', args=None):
    """
    :param browser:
    :param args:
    :rtype: RemoteDriver
    :return:
    """
    if browser not in BROWSER_MAPPING.keys():
        raise RuntimeError("unknown browser %s. allowed: %s" % (browser, ", ".join(BROWSER_MAPPING.keys())))
    driver_cls = BROWSER_MAPPING.get(browser)
    safe_args = {}
    if args is not None:
        expected_arguments = inspect.getargspec(driver_cls.__init__).args
        expected_arguments.remove("self")
        for arg in expected_arguments:
            if arg in args:
                safe_args[arg] = args[arg]
    return driver_cls(**safe_args)
