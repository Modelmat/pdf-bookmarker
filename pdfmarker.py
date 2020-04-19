from anytree import Node
from operator import getitem
from pdfrw import PdfReader, PdfArray
from roman import to_roman
from string import ascii_lowercase, ascii_uppercase
from typing import List, Optional


PREFACE_FORMAT = """\
[ /Title ({title})
  /Author ({author})
  /DOCINFO pdfmark

"""
TITLE_PREFACE_FORMAT = """\
[ /Title ({title})
  /DOCINFO pdfmark

"""
AUTHOR_PREFACE_FORMAT = """\
[ /Author ({author})
  /DOCINFO pdfmark

"""
ENTRY_FORMAT = """\
[ /Title ({name}) /Page {page} /OUT pdfmark
"""
# negative numbers have all the entries closed by default
# positive numbers have them open by default
HEADER_FORMAT = """\
[ /Count -{number_of_children} /Title ({name}) /Page {page} /OUT pdfmark
"""


def parse_page_labels(page_labels: PdfArray, number_pages: int) -> List[str]:
    page_numbers = []

    # add the final stop position
    page_labels.append(number_pages)

    for i in range(0, len(page_labels) - 1, 2):
        start, options, stop = page_labels[i : i + 3]
        stop = int(stop)
        start = int(start)

        # /S specifies the numbering style for page numbers:
        #   /D - Arabic numerals (1,2,3...)
        #   /r - lowercase Roman numerals (i, ii, iii,...)
        #   /R - uppercase Roman numerals (I, II, III,...)
        #   /A - uppercase letters (A-Z)
        #   /a - lowercase letters (a-z)
        # /P (optional) - page number prefix
        # /St (optional) - the value of the first page number in the range (default: 1)
        page_offset = options.St or 1
        page_range = range(page_offset, (stop - start) + 1)

        option_mapping = {
            "/D": str,
            "/r": lambda x: to_roman(x).lower(),
            "/R": to_roman,
            "/a": ascii_lowercase.__getitem__,
            "/A": ascii_uppercase.__getitem__,
        }

        range_numbers = map(option_mapping.get(options.S), page_range)

        if options.P is not None:
            range_numbers = map(lambda x: options.P + x, range_numbers)

        page_numbers.extend(range_numbers)

    return page_numbers


def adjust_page_number(page_number: str, page_numbers: List[str]) -> int:
    """Adjusts the page number to be one indexed from the start of the PDF
    
    Many TOC use special page numbers (e.g. xxv) in the prefaces and this
    is reflected in the table of contents. However, these page numbers are not
    used in pdfmark generation, instead the standard 1 to N pages being used.
    
    Hence, this function converts the special numbers to standard page numbers
    by reading PDF metadata and then offsetting the given integer numbers by
    the amount of special numbers.
    
    Information on the PageLabels specification is located at:
    https://www.w3.org/TR/WCAG20-TECHS/PDF17.html
    """

    return page_numbers.index(page_number) + 1


def get_page_numbers(input_pdf_path: str, offset: int = 0) -> List[str]:
    pdf = PdfReader(input_pdf_path)
    page_labels = pdf.Root.PageLabels
    number_pages = len(pdf.pages)

    if page_labels is not None and page_labels.Nums is not None:
        return parse_page_labels(page_labels.Nums, number_pages)
    else:
        print(
            "[warning] input PDF does not have pageLabels, "
            "page numbers may be incorrect"
        )
        return [str(i + offset) for i in range(1, number_pages + 1)]


def generate_pdfmarks(
    root_node: Node,
    page_numbers: List[str],
    title: Optional[str] = None,
    author: Optional[str] = None,
    output: Optional[List[str]] = None,
) -> str:
    if output is None:
        output = []

        if author is not None and title is not None:
            output.append(PREFACE_FORMAT.format(title=title, author=author))

        elif author is not None:
            # hence title must not exist
            output.append(AUTHOR_PREFACE_FORMAT.format(author=author))

        elif title is not None:
            output.append(TITLE_PREFACE_FORMAT.format(title=title))

    output = output or [PREFACE_FORMAT.format(title=title, author=author)]

    for node in root_node.children:
        # purely a cosmetic thing so the generated file is readable
        output.append("  " * node.depth)

        page_number = adjust_page_number(node.page, page_numbers)
        if node.children:
            output.append(
                HEADER_FORMAT.format(
                    number_of_children=len(node.children),
                    name=node.name,
                    page=page_number,
                )
            )
            generate_pdfmarks(node, page_numbers, output=output)
            output.append("\n")
        else:
            output.append(ENTRY_FORMAT.format(name=node.name, page=page_number))

    return "".join(output)
