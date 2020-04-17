# PDF Bookmarker

A Python script to allow bookmarks to be added to a PDF.
Current solutions such as PyPDF2 and pdfrw either do not have bookmark support, 
or they does not retain special page numbers such as `xxv` or offset ones when writing.

Ghostscript, combined with a postscript instruction file, will, and this script generates
a table of contents tree from a flat tree (see the example table of contents text file)
which is then converted into a `.ps` file to be added to a PDF through `gs`.

## Usage
**TODO**: none of these work, script must be modified manually
**TODO**: allow adjustable page offset (roman numerals -> normal numbers, or just general offset)

Generates a .ps file from a flat table of contents tree
```py
python bookmarker.py generate-ps --input=table-of-contents.txt --output=bookmarks.ps
```

Adds a postscript file bookmarks to a PDF. Runs ghostscripts behind the scenes.
```py
python bookmarker.py apply-ps --ps=bookmarks.ps --pdf=coding-tutorial.pdf --output=awesome-coding-tutorial.pdf
```

Generates the postscript file and then applies it
```py
python bookmarker.py add-bookmarks --input=table-of-contents.txt --pdf=coding-tutorial.pdf --output=awesome-coding-tutorial.pdf
```
