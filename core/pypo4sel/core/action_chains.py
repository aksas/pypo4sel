import time

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.command import Command

from .common import WAIT_STALE_ELEMENT_MAX_TRY, WAIT_ELEMENT_POLL_FREQUENCY


class ActionChains(webdriver.ActionChains):
    def __move_to(self, element, xoffset=None, yoffset=None):
        params = {'element': element.id}
        if xoffset is not None and yoffset is not None:
            params.update({'xoffset': int(xoffset),
                           'yoffset': int(yoffset)})

        def loop():
            attempt = 0
            while attempt < WAIT_STALE_ELEMENT_MAX_TRY:
                try:
                    self._driver.execute(Command.MOVE_TO, params)
                    break
                except StaleElementReferenceException:
                    time.sleep(WAIT_ELEMENT_POLL_FREQUENCY)
                    element.reload()
                    params['element'] = element.id
                attempt += 1

        return loop

    def move_to_element_with_offset(self, to_element, xoffset, yoffset):
        self._actions.append(self.__move_to(to_element, xoffset, yoffset))
        return self

    def move_to_element(self, to_element):
        self._actions.append(self.__move_to(to_element))
        return self


class TouchActions(webdriver.TouchActions):
    def __safe_execute(self, driver_command, element, param=None):
        param = {} if param is None else param
        attempt = 0
        while attempt < WAIT_STALE_ELEMENT_MAX_TRY:
            try:
                param['element'] = element.id
                self._driver.execute(driver_command, param)
                break
            except StaleElementReferenceException:
                time.sleep(WAIT_ELEMENT_POLL_FREQUENCY)
                element.reload()
            attempt += 1

    def tap(self, on_element):
        """
        Taps on a given element.

        Args:
            on_element: The element to tap.
        """
        self._actions.append(lambda: self.__safe_execute(Command.SINGLE_TAP, on_element))
        return self

    def double_tap(self, on_element):
        """
        Double taps on a given element.

        Args:
            on_element: The element to tap.
        """
        self._actions.append(lambda: self.__safe_execute(Command.DOUBLE_TAP, on_element))
        return self

    def scroll_from_element(self, on_element, xoffset, yoffset):
        """
        Touch and scroll starting at on_element, moving by xoffset and yoffset.

        Args:
          on_element: The element where scroll starts.
          xoffset: X offset to scroll to.
          yoffset: Y offset to scroll to.
        """
        self._actions.append(lambda: self.__safe_execute(Command.TOUCH_SCROLL, on_element,
                                                         {'xoffset': int(xoffset),
                                                          'yoffset': int(yoffset)}))
        return self

    def long_press(self, on_element):
        """
        Long press on an element.

        Args:
          on_element: The element to long press.
        """
        self._actions.append(lambda: self.__safe_execute(Command.LONG_PRESS, on_element))
        return self

    def flick_element(self, on_element, xoffset, yoffset, speed):
        """
        Flick starting at on_element, and moving by the xoffset and yoffset
        with specified speed.

        Args:
          on_element: Flick will start at center of element.
          xoffset: X offset to flick to.
          yoffset: Y offset to flick to.
          speed: Pixels per second to flick.
        """
        self._actions.append(lambda: self.__safe_execute(Command.FLICK, on_element, {
            'xoffset': int(xoffset),
            'yoffset': int(yoffset),
            'speed': int(speed)}))
        return self
