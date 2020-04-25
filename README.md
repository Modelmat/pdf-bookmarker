# PDF Bookmarker

A Python script to allow bookmarks to be added to a PDF.
Current solutions such as PyPDF2 and pdfrw either do not have bookmark support, 
or they does not retain special page numbers such as `xxv` or offset ones when writing.

Ghostscript, combined with a postscript instruction file, will, and this script generates
a table of contents tree from a flat tree (see the example table of contents text file)
which is then converted into a `.ps` file to be added to a PDF through `gs`.

## Installation
1. Install the python requirements:
```bash
$ pip install anytree pdfrw Gooey
```
2. Install ghostscript. Ensure `gs` is in path.
```bash
$ sudo pacman -Syu ghostscript
```

## Usage
**TODO**: Document how to add custom level functions through python module.

By default this opens in GUI using Gooey, however the "--ignore-gooey" allows
the CLI interface to be used.

### Example 1: Bookmark using Indentation Level
This is the default style.
```bash
$ python bookmarker.py examples/indentation/cambridge-maths-ext1-y11.txt \
    input.pdf out.pdf \
    --ignore-gooey \
    --title="Cambridge Mathematics Extension 1 Year 11" \
    --author="Bill Pender et al"
```

### Example 2: Bookmark using regex style 1
```bash
$ python bookmarker.py examples/regex/programming-principles-and-practice-using-c++.txt \
    input.pdf out.pdf \
    --ignore-gooey \
    --title="Programming Principles and Practice Using C++" \
    --author="Bjarne Stroustrup" \
    --format=regex-1
```
