# -*- coding: utf-8 -*-

#  Copyright 2010 Adam Zapletal
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import re
import sys

SUPPORTED_FORMATS = {
    'markdown':         ['.mdown', '.markdown', '.markdn', '.md', '.mdn'],
    'restructuredtext': ['.rst', '.rest'],
    'textile':          ['.textile'],
}

SUPPORTED_DRIVERS = {
    'markdown':         ['misaka', 'markdown'],
    'restructuredtext': ['rst'],
    'textile':          ['textile'],
}


class Parser(object):
    """This class generates the HTML code depending on which syntax is used in
       the souce document.

       The Parser currently supports both Markdown and restructuredText
       syntaxes.
    """
    RST_REPLACEMENTS = [
            (r'<div.*?>', r'', re.UNICODE),
            (r'</div>', r'', re.UNICODE),
            (r'<p class="system-message-\w+">.*?</p>', r'', re.UNICODE),
            (r'Document or section may not begin with a transition\.',
             r'', re.UNICODE),
            (r'<h(\d+?).*?>', r'<h\1>', re.DOTALL | re.UNICODE),
            (r'<hr.*?>\n', r'<hr />\n', re.DOTALL | re.UNICODE),
    ]
    md_extensions = ''

    def __init__(self, extension, driver=None, encoding='utf8',
                 md_extensions='', logger=sys.stderr):
        """Configures this parser.
        """
        self.encoding = encoding
        self.format = None
        self.driver = None
        self.logger = logger

        for supp_format, supp_extensions in SUPPORTED_FORMATS.items():
            for supp_extension in supp_extensions:
                if supp_extension == extension:
                    self.format = supp_format
        if not self.format:
            raise NotImplementedError(u"Unsupported format %s" % extension)

        alternatives = SUPPORTED_DRIVERS[self.format]
        if driver:
            if driver not in SUPPORTED_DRIVERS[self.format]:
                raise RuntimeError(u"Unsupported driver %s for format %s"
                                   % (driver, self.format))
            alternatives = [driver]
        for alternative in alternatives:
            try:
                self.module = __import__(alternative)
                self.driver = alternative
                break
            except ImportError:
                pass
        if not self.driver:
            raise RuntimeError(u"Looks like required module is not installed "
                                "for format %s; supported modules: %s" %
                               (self.format, SUPPORTED_DRIVERS[self.format]))

        # TODO: Make this usable for all drivers (how?)
        if md_extensions:
            exts = (value.strip() for value in md_extensions.split(','))
            self.md_extensions = filter(None, exts)

    def parse(self, text):
        """Parses and renders a text as HTML regarding current format.
        """
        if self.driver == 'markdown':
            if text.startswith(u'\ufeff'):  # check for unicode BOM
              text = text[1:]

            return self.module.markdown(text, self.md_extensions)
        elif self.driver == 'misaka':
            if text.startswith(u'\ufeff'):  # check for unicode BOM
              text = text[1:]
            m = self.module
            return m.html(text,
                render_flags=
                    m.HTML_USE_XHTML |
                    m.HTML_SMARTYPANTS,
                extensions=
                    m.EXT_NO_INTRA_EMPHASIS |
                    m.EXT_FENCED_CODE |
                    m.EXT_SUPERSCRIPT |
                    m.EXT_AUTOLINK |
                    m.EXT_STRIKETHROUGH |
                    m.EXT_TABLES
            )
        elif self.driver == 'rst':
            html = self.module.html_body(text, input_encoding=self.encoding)
            # RST generates pretty much markup to be removed in our case
            for (pattern, replacement, mode) in self.RST_REPLACEMENTS:
                html = re.sub(re.compile(pattern, mode), replacement, html, 0)
            return html.strip()
        elif self.driver == 'textile':
            return self.module.textile(text, encoding=self.encoding)
        else:
            raise NotImplementedError(u"Unsupported format %s, cannot parse"
                                      % self.format)
