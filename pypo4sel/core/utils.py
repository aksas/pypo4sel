from HTMLParser import HTMLParser

__all__ = ["self_text", "inner_text"]


class _ParseText(HTMLParser):
    def __init__(self, text):
        HTMLParser.__init__(self)
        self.self_text = ""
        self.inner_text = ""
        self.__tags = []
        self.feed(text)

    def handle_starttag(self, tag, attr):
        self.__tags.append((tag, ""))

    def handle_endtag(self, tag):
        n, text = self.__tags.pop()
        while n != tag:
            n, t = self.__tags.pop()
            text = t + text
        if len(self.__tags) == 0:
            self.self_text = text

    def handle_data(self, data):
        self.inner_text += data
        n, t = self.__tags[-1]
        self.__tags[-1] = n, t + data


def self_text(element):
    inner_html = u"<el_wrap>{0}</el_wrap>".format(element.get_attribute('innerHTML')).encode('utf-8')
    return _ParseText(inner_html).self_text


def inner_text(element):
    inner_html = u"<el_wrap>{0}</el_wrap>".format(element.get_attribute('innerHTML')).encode('utf-8')
    return _ParseText(inner_html).inner_text
