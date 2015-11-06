from HTMLParser import HTMLParser

__all__ = ["self_text", "inner_text"]

"""
blockquote
br
dd
dt
h1-h6
hr
li
p
"""

tag_map = ['blockquote', 'br', 'dd', 'dt', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'li', 'p']


class _ParseText(HTMLParser):
    wrap_start = ['blockquote', 'li', 'dd', 'dt', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'p']
    wrap_end = ['blockquote', 'br', 'ul', 'ol', 'dl' 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'p']

    def __init__(self, text):
        HTMLParser.__init__(self)
        self.self_text = ""
        self.inner_text = ""
        self.__tags = []
        self.feed(text)

    def handle_starttag(self, tag, attr):
        first_char = ""
        if len(self.__tags) > 1 and tag in self.wrap_start:
            first_char = " "
        self.__tags.append((tag, first_char))

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


class Mock(object):
    def __init__(self, text):
        super(Mock, self).__init__()
        self.text = text

    def get_attribute(self, t):
        return self.text


if __name__ == '__main__':
    t = Mock("<h1><b>h1 text</h1>text<p>textp<br>oooo")
    print self_text(t)
    print inner_text(t)
