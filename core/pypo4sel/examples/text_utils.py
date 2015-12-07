from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint

__all__ = ["self_text", "inner_text"]


# noinspection PyAbstractClass
class ParseText(HTMLParser):
    wrap_start = ['blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'p', 'br', 'li', 'dd', 'dt']
    wrap_end = ['blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'p', 'ul', 'ol', 'dl']

    def __init__(self, text):
        HTMLParser.__init__(self)
        self.self_text = u""
        self.inner_text = u""
        self.__tags = []
        self.feed(text)

    def handle_starttag(self, tag, attr):
        if tag in self.wrap_start and self.inner_text:
            self.inner_text += u" "
            n, t = self.__tags[-1]
            self.__tags[-1] = n, t + u" "
        self.__tags.append((tag, u""))

    def handle_endtag(self, tag):
        n, text = self.__tags.pop()
        while n != tag:
            n, t = self.__tags.pop()
            text = t + text
        if len(self.__tags) == 0:
            self.self_text = text
        elif tag in self.wrap_end:
            self.inner_text += u" "

    def handle_data(self, data):
        self.inner_text += data
        n, t = self.__tags[-1]
        self.__tags[-1] = n, t + data

    def handle_entityref(self, name):
        self.handle_data(unichr(name2codepoint[name]))

    def handle_charref(self, name):
        if name[0] == 'x':
            n = int(name[1:], 16)
        else:
            n = int(name)
        self.handle_data(unichr(n))


def self_text(element):
    inner_html = u"<el_wrap>{0}</el_wrap>".format(element.get_attribute('innerHTML'))
    return ParseText(inner_html).self_text


def inner_text(element):
    inner_html = u"<el_wrap>{0}</el_wrap>".format(element.get_attribute('innerHTML'))
    return ParseText(inner_html).inner_text
