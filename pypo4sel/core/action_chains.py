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
