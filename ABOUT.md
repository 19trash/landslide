The original [Landslide](https://github.com/adamzap/landslide) is a great
software to create html5 slides (thanks Adam Zapletal).  In this fork, I've made
some invasive changes listed below.  Due to my time constraints, I couldn't
fully document all of them.  Note that, some of the changes were also sent to
upstream as pull requests.  But due to the same time constraints, I can't
maintain them on separate branches any more.

Users of Debian (and derivates) may want to install `python-landslide-patched`
package by adding our repository: http://deb.ondokuz.biz and issuing the
following commands:

    sudo apt-get install python-landslide-patched

To use sundown parser, please also install `python-misaka` package:

    sudo apt-get install python-misaka

## Changes

### Add support for Misaka: Sundown parser for Python

See http://misaka.61924.nl/.

### Support code highlighting in fenced code blocks

Most Markdown parsers which support fenced code blocks, emit the following
output:

        <pre><code class="python">...</code></pre>

for the fenced block:

        ```python
        ...
        ```

In code highlighting macro, add a new regular expression pattern to handle such
cases.

#### New macros

- `.code`, `.coden` and `.include` to include external files

  + `.code: <file>.ext`: include `<file>.ext`, located via `includepath`, as a
    code block. (language is recognized by `.ext`)

  + `.coden: <file>.ext`: like `.code`, but with linenos.

  + `.include: <file>`: raw include.

- `.gist` to include a gist in whole or parts

  + Whole content in Gist 123456:

            .gist: 123456

  + Only the files `foo` and `bar`:

            .gist: 123456 foo bar


- Add code to setup `includepath` and `expandtabs` via command line and
  configuration file.

- Current directory is always in `includepath`.

### Allow setting expandtabs per included file

Embed `expandtabs` value in include macro names, e.g. `.code4` means a value of
4 for `expandtabs`.  Somewhat a hack in the lack of "per macro configuration"
mechanism.

### Enable linenos per code blocks

- Using a pound before bang enables linenos for the codeblock.  Example:

        #!python
        ...

- Similar syntax in fenced code blocks.  Example:

        ```#python
        ...
        ```

### Fix and improve embedding images in CSS files

Embedding images from user css files (defined in configuration) were failed due
to handling of relative paths, ie paths were relative to the THEMES_DIR.
Relative image paths should be relative to the directory which the CSS file
resides.

### Enhancements for touch screen devices

- Add navigation menu bars on both sides.  Menu bars are vertically placed on
  each sides because some browsers (e.g. GoodReader on iOS) use top and bottom
  edges.

- Disable context on screens having resolution smaller than 1280px.

- On iOS devices, allow browsing slides in full-screen by adding the meta tag
  "apple-mobile-web-app-capable".  Now iOS users can save the slides to their
  home screens and view the slides in full-screen with Safari.

- Disable user zooming.  FIXME Make this optional.

- Add a hack for iPhone/iPod to fix navigation hover issues

### Various enhancements for pre areas

- Limit pre area's height and allow using a vertical scrollbar for overflowed
  content (I think this might be considered as the most appealing reason for
  using html slides involving codes).

- Render a nice vertical scrollbar for overflowed pre areas.

- Add a few space after linenos.

- Support Github's Gist for consistency.

- Add new fixed width fonts to prevent falling back to Courier.
