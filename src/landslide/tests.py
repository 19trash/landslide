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

import macro
import os
import re
import unittest
import codecs

from generator import Generator
from parser import Parser


SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'samples')
if (not os.path.exists(SAMPLES_DIR)):
    raise IOError('Sample source files not found, cannot run tests')


class BaseTestCase(unittest.TestCase):
    def logtest(self, message, type='notice'):
        if type == 'warning':
            raise WarningMessage(message)
        elif type == 'error':
            raise ErrorMessage(message)


class GeneratorTest(BaseTestCase):
    def test___init__(self):
        self.assertRaises(IOError, Generator, None)
        self.assertRaises(IOError, Generator, 'foo.md')

    def test_add_user_assets(self):
        base_dir = os.path.join(SAMPLES_DIR, 'example1', 'slides.md')
        g = Generator(base_dir, logger=self.logtest)
        g.add_user_css(os.path.join(SAMPLES_DIR, 'test.css'))
        g.add_user_js(os.path.join(SAMPLES_DIR, 'test.js'))
        self.assertEquals(g.user_css[0]['contents'], '* {color: red;}')
        self.assertEquals(g.user_js[0]['contents'], "alert('foo');")

    def test_get_toc(self):
        base_dir = os.path.join(SAMPLES_DIR, 'example1', 'slides.md')
        g = Generator(base_dir, logger=self.logtest)
        g.add_toc_entry('Section 1', 1, 1)
        g.add_toc_entry('Section 1.1', 2, 2)
        g.add_toc_entry('Section 1.2', 2, 3)
        g.add_toc_entry('Section 2', 1, 4)
        g.add_toc_entry('Section 2.1', 2, 5)
        g.add_toc_entry('Section 3', 1, 6)
        toc = g.toc
        self.assertEquals(len(toc), 3)
        self.assertEquals(toc[0]['title'], 'Section 1')
        self.assertEquals(len(toc[0]['sub']), 2)
        self.assertEquals(toc[0]['sub'][1]['title'], 'Section 1.2')
        self.assertEquals(toc[1]['title'], 'Section 2')
        self.assertEquals(len(toc[1]['sub']), 1)
        self.assertEquals(toc[2]['title'], 'Section 3')
        self.assertEquals(len(toc[2]['sub']), 0)

    def test_get_slide_vars(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example1', 'slides.md'))
        svars = g.get_slide_vars("<h1>heading</h1>\n<p>foo</p>\n<p>bar</p>\n")
        self.assertEquals(svars['title'], 'heading')
        self.assertEquals(svars['level'], 1)
        self.assertEquals(svars['header'], '<h1>heading</h1>')
        self.assertEquals(svars['content'], '<p>foo</p>\n<p>bar</p>')
        self.assertEquals(svars['source'], {})
        self.assertEquals(svars['classes'], [])

    def test_unicode(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example3', 'slides.rst'))
        g.execute()
        s = g.render()
        self.assertTrue(s.find('<pre>') != -1)
        self.assertEquals(len(re.findall('<pre><span', s)), 3)

    def test_inputencoding(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example3',
            'slides.koi8_r.rst'), encoding='koi8_r')
        content = g.render()
        # check that the string is utf_8
        self.assertTrue(re.findall(u'русский', content,
            flags=re.UNICODE))
        g.execute()
        file_contents = codecs.open(g.destination_file, encoding='utf_8')\
            .read()
        # check that the file was properly encoded in utf_8
        self.assertTrue(re.findall(u'русский', file_contents,
            flags=re.UNICODE))

    def test_get_template_vars(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example1', 'slides.md'))
        svars = g.get_template_vars([{'title': "slide1", 'level': 1},
                                     {'title': "slide2", 'level': 1},
                                     {'title': None, 'level': 1},
                                    ])
        self.assertEquals(svars['head_title'], 'slide1')

    def test_process_macros(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example1', 'slides.md'))
        # Notes
        r = g.process_macros('<p>foo</p>\n<p>.notes: bar</p>\n<p>baz</p>')
        self.assertEquals(r[0].find('<p class="notes">bar</p>'), 11)
        self.assertEquals(r[1], [u'has_notes'])
        # FXs
        content = '<p>foo</p>\n<p>.fx: blah blob</p>\n<p>baz</p>'
        r = g.process_macros(content)
        self.assertEquals(r[0], '<p>foo</p>\n<p>baz</p>')
        self.assertEquals(r[1][0], 'blah')
        self.assertEquals(r[1][1], 'blob')

    def test_register_macro(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example1', 'slides.md'))

        class SampleMacro(macro.Macro):
            pass

        g.register_macro(SampleMacro)
        self.assertTrue(SampleMacro in g.macros)

        def plop(foo):
            pass

        self.assertRaises(TypeError, g.register_macro, plop)

    def test_presenter_notes(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example1', 'slides.md'))
        svars = g.get_slide_vars("<h1>heading</h1>\n<p>foo</p>\n"
                                 "<h1>Presenter Notes</h1>\n<p>bar</p>\n")
        self.assertEquals(svars['presenter_notes'], "<p>bar</p>")

    def test_skip_presenter_notes(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example1', 'slides.md'),
                presenter_notes=False)
        svars = g.get_slide_vars("<h1>heading</h1>\n<p>foo</p>\n"
                                 "<h1>Presenter Notes</h1>\n<p>bar</p>\n")
        self.assertEquals(svars['presenter_notes'], None)


class CodeHighlightingMacroTest(BaseTestCase):
    def setUp(self):
        self.sample_html = '''<p>Let me give you this snippet:</p>
<pre class="literal-block">
!python
def foo():
    &quot;just a test&quot;
    print bar
</pre>
<p>Then this one:</p>
<pre class="literal-block">
!php
<?php
echo $bar;
?>
</pre>
<p>Then this other one:</p>
<pre class="literal-block">
!!xml
<foo>
    <bar glop="yataa">baz</bar>
</foo>
</pre>
<p>End here.</p>'''

    def test_parsing_code_blocks(self):
        m = macro.CodeHighlightingMacro(self.logtest)
        blocks = m.banged_blocks_re.finditer(self.sample_html)
        match = blocks.next()
        self.assertEquals(match.group('lang'), 'python')
        self.assertTrue(match.group('code').startswith('def foo():'))
        match = blocks.next()
        self.assertEquals(match.group('lang'), 'php')
        self.assertTrue(match.group('code').startswith('<?php'))
        match = blocks.next()
        self.assertEquals(match.group('lang'), 'xml')
        self.assertTrue(match.group('code').startswith('<foo>'))
        with self.assertRaises(StopIteration):
            blocks.next()

    def test_descape(self):
        m = macro.CodeHighlightingMacro(self.logtest)
        self.assertEquals(m.descape('foo'), 'foo')
        self.assertEquals(m.descape('&gt;'), '>')
        self.assertEquals(m.descape('&lt;'), '<')
        self.assertEquals(m.descape('&amp;lt;'), '&lt;')
        self.assertEquals(m.descape('&lt;span&gt;'), '<span>')
        self.assertEquals(m.descape('&lt;spam&amp;eggs&gt;'), '<spam&eggs>')

    def test_process(self):
        m = macro.CodeHighlightingMacro(self.logtest)
        hl = m.process("<pre><code>!php\n$foo;</code></pre>")
        self.assertTrue(hl[0].startswith('<div class="highlight"><pre'))
        self.assertEquals(hl[1][0], u'has_code')
        input = "<p>Nothing to declare</p>"
        self.assertEquals(m.process(input)[0], input)
        self.assertEquals(m.process(input)[1], [])

    def test_process_rst_code_blocks(self):
        m = macro.CodeHighlightingMacro(self.logtest)
        hl = m.process(self.sample_html)
        self.assertTrue(hl[0].startswith('<p>Let me give you this'))
        self.assertTrue(hl[0].find('<p>Then this one') > 0)
        self.assertTrue(hl[0].find('<p>Then this other one') > 0)
        self.assertTrue(hl[0].find('<div class="highlight"><pre') > 0)
        self.assertEquals(hl[1][0], u'has_code')


class EmbedImagesMacroTest(BaseTestCase):
    def test_process(self):
        base_dir = os.path.join(SAMPLES_DIR, 'example1', 'slides.md')
        m = macro.EmbedImagesMacro(self.logtest, True)
        self.assertRaises(WarningMessage, m.process,
                          '<img src="toto.jpg"/>', '.')
        content, classes = m.process('<img src="monkey.jpg"/>', base_dir)
        self.assertTrue(re.match(r'<img src="data:image/jpeg;base64,(.+?)"/>',
                        content))


class FixImagePathsMacroTest(BaseTestCase):
    def test_process(self):
        base_dir = os.path.join(SAMPLES_DIR, 'example1', 'slides.md')
        m = macro.FixImagePathsMacro(self.logtest, False)
        content, classes = m.process('<img src="monkey.jpg"/>', base_dir)
        self.assertTrue(re.match(r'<img src="file://.*?/monkey.jpg" */>',
                                 content))


class FxMacroTest(BaseTestCase):
    def test_process(self):
        m = macro.FxMacro(self.logtest)
        content = '<p>foo</p>\n<p>.fx: blah blob</p>\n<p>baz</p>'
        r = m.process(content)
        self.assertEquals(r[0], '<p>foo</p>\n<p>baz</p>')
        self.assertEquals(r[1][0], 'blah')
        self.assertEquals(r[1][1], 'blob')


class NotesMacroTest(BaseTestCase):
    def test_process(self):
        m = macro.NotesMacro(self.logtest)
        r = m.process('<p>foo</p>\n<p>.notes: bar</p>\n<p>baz</p>')
        self.assertEquals(r[0].find('<p class="notes">bar</p>'), 11)
        self.assertEquals(r[1], [u'has_notes'])


class IncludeMacroTest(BaseTestCase):
    def test_process_whole_file(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        content, classes = m.process('<p>.coden: src/day.c</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*stdio\.h', content))
        self.assertTrue(re.search(r'"lineno"> *22<.*>}<', content))
        self.assertFalse(re.search(r'"lineno"> *23<', content))
    def test_process_oneline_num_positive(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        content, classes = m.process('<p>.coden: src/day.c 8</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*wednesday', content))
        self.assertFalse(re.search(r'"lineno"> *2<', content))
    def test_process_oneline_num_negative(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        content, classes = m.process('<p>.coden: src/day.c -1</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*>}<', content))
        self.assertFalse(re.search(r'"lineno"> *2<', content))
    def test_process_oneline_dollar(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        content, classes = m.process('<p>.coden: src/day.c $</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*>}<', content))
        self.assertFalse(re.search(r'"lineno"> *2<', content))
    def test_process_oneline_pattern(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        content, classes = m.process('<p>.coden: src/day.c /.+wednesday/</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*wednesday', content))
        self.assertFalse(re.search(r'"lineno"> *2<', content))
    def test_process_oneline_errors(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        self.assertRaises(WarningMessage, m.process,
                          '<p>.code: src/day.c /foo/</p>', source)
        self.assertRaises(WarningMessage, m.process,
                          '<p>.code: src/day.c 1000</p>', source)
        self.assertRaises(WarningMessage, m.process,
                          '<p>.code: src/day.c -1000</p>', source)
    def test_process_multiline_pattern(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        content, classes = m.process('<p>.coden: src/day.c /.+wednesday/ /.+friday/</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*wednesday', content))
        self.assertTrue(re.search(r'"lineno"> *2<.*thursday', content))
        self.assertTrue(re.search(r'"lineno"> *3<.*friday', content))
        self.assertFalse(re.search(r'"lineno"> *4<', content))
    def test_process_multiline_num_positive(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        content, classes = m.process('<p>.coden: src/day.c 8 10</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*wednesday', content))
        self.assertTrue(re.search(r'"lineno"> *2<.*thursday', content))
        self.assertTrue(re.search(r'"lineno"> *3<.*friday', content))
        self.assertFalse(re.search(r'"lineno"> *4<', content))
    def test_process_multiline_num_negative(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        content, classes = m.process('<p>.coden: src/day.c -15 -13</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*wednesday', content))
        self.assertTrue(re.search(r'"lineno"> *2<.*thursday', content))
        self.assertTrue(re.search(r'"lineno"> *3<.*friday', content))
        self.assertFalse(re.search(r'"lineno"> *4<', content))
    def test_process_multiline_errors(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        self.assertRaises(WarningMessage, m.process,
                          '<p>.code: src/day.c /foo/ /bar/</p>', source)
        self.assertRaises(WarningMessage, m.process,
                          '<p>.code: src/day.c 11 7</p>', source)
        self.assertRaises(WarningMessage, m.process,
                          '<p>.code: src/day.c -5 -10</p>', source)
    def test_process_offset_simple(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        content, classes = m.process('<p>.coden: src/day.c /main\(.+\)/- /}/</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*int', content))
        self.assertTrue(re.search(r'"lineno"> *2<.*main', content))
        self.assertTrue(re.search(r'"lineno"> *9<.*}', content))
        self.assertFalse(re.search(r'"lineno"> *10<', content))
    def test_process_offset_fancy(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        content, classes = m.process('<p>.coden: src/day.c /static.const.char.+day/+2 /}/-</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*monday', content))
        self.assertTrue(re.search(r'"lineno"> *7<.*sunday', content))
        self.assertFalse(re.search(r'"lineno"> *8<', content))
    def test_process_offset_errors(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        self.assertRaises(WarningMessage, m.process,
                          '<p>.code: src/day.c /main/+8</p>', source)
        self.assertRaises(WarningMessage, m.process,
                          '<p>.code: src/day.c /main/-15</p>', source)
        self.assertRaises(WarningMessage, m.process,
                          '<p>.code: src/day.c /main/+4 /}/-4</p>', source)
    def test_process_option_includepath(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        includepath_old = m.options['includepath']
        m.options['includepath'] = '.'
        self.assertRaises(WarningMessage, m.process,
                          '<p>.coden: day.c /.+wednesday/</p>', source)
        content, classes = m.process('<p>.coden: src/day.c /.+wednesday/</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*wednesday', content))
        m.options['includepath'] = includepath_old
    def test_process_option_expandtabs(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        expandtabs_old = m.options['expandtabs']
        ts = m.options['expandtabs'] = 4
        content, classes = m.process('<p>.coden: src/day.c /.+wednesday/</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*>\s?[ ]{' + str(ts) + '}<.*wednesday', content))
        ts = m.options['expandtabs'] = 12
        content, classes = m.process('<p>.coden: src/day.c /.+wednesday/</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*>\s?[ ]{' + str(ts) + '}<.*wednesday', content))
        m.options['expandtabs'] = expandtabs_old
    def test_process_option_expandtabs_per_macro(self):
        source = os.path.join(SAMPLES_DIR, 'example5', 'slides.md')
        m = macro.IncludeMacro(self.logtest)
        ts = 2
        content, classes = m.process('<p>.coden' + str(ts) + ': src/day.c /.+wednesday/</p>', source)
        self.assertTrue(re.search(r'"lineno"> *1<.*>\s?[ ]{' + str(ts) + '}<.*wednesday', content))


class ParserTest(BaseTestCase):
    def test___init__(self):
        self.assertEquals(Parser('.md', logger=self.logtest).format, 'markdown')
        self.assertEquals(Parser('.markdown', logger=self.logtest).format, 'markdown')
        self.assertEquals(Parser('.rst', logger=self.logtest).format, 'restructuredtext')
        self.assertRaises(NotImplementedError, Parser, '.txt')


class WarningMessage(Exception):
    pass


class ErrorMessage(Exception):
    pass

if __name__ == '__main__':
    unittest.main()
