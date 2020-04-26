from anytree import Node, RenderTree
import re
from gooey import Gooey, GooeyParser
from typing import List, Tuple, Optional
import platform
import os
import tempfile
import subprocess
import sys
import toc_parser as parser
import pdfmarker


def is_valid_file(arg):
    if not os.path.isfile(arg):
        raise argparse.ArgumentTypeError("The file {0} does not exist".format(arg))
    else:
        return arg


def file_contents(arg):
    try:
        with open(arg, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise argparse.ArgumentTypeError("The file {0} does not exist".format(arg))


@Gooey(
    progress_regex=r"^\[progress\]: (?P<current>\d+)/(?P<total>\d+)$",
    hide_progress_msg=True,
    progress_expr="current / total * 100",
)
def parse_arguments() -> Tuple[List[str], str, str]:
    main_parser = GooeyParser(
        description="Add bookmarks to a PDF from a table of contents"
    )
    main_parser.add_argument(
        "table_of_contents",
        help="The path to the table of contents text file",
        type=file_contents,
        widget="FileChooser",
    )
    main_parser.add_argument(
        "input_path",
        help="The original unbookmarked PDF",
        type=is_valid_file,
        widget="FileChooser",
    )
    main_parser.add_argument(
        "output_path",
        help="The path to write the bookmarked PDF to",
        widget="FileChooser",
    )
    main_parser.add_argument("--title", help="The book title", default=None)
    main_parser.add_argument("--author", help="The book author", default=None)
    main_parser.add_argument(
        "-f",
        "--format",
        help="Format to determine how the table of contents is broken into different levels",
        default="indents",
        choices=parser.get_valid_formats(),
    )
    main_parser.add_argument(
        "-p",
        "--print_tree",
        help="Prints out the bookmark tree rather than add to PDF",
        action="store_true",
        default=False,
    )
    main_parser.add_argument(
        "--pdfmarks_save_path",
        help="The path to save the pdfmarks. If not supplied, a temp file will be created.",
    )
    main_parser.add_argument(
        "-r",
        "--remove_bookmarks",
        help="Whether to strip bookmarks from the input PDF.",
        action="store_true",
        default=False,
    )

    args = main_parser.parse_args()
    return (
        args.table_of_contents.split("\n"),
        args.input_path,
        args.output_path,
        args.format,
        args.print_tree,
        args.title,
        args.author,
        args.pdfmarks_save_path,
        args.remove_bookmarks,
    )


def main(
    table_of_contents: List[str],
    input_path: str,
    output_path: str,
    format: Optional[str] = "indents",
    print_tree: Optional[bool] = False,
    title: Optional[str] = None,
    author: Optional[str] = None,
    pdfmarks_save_path: Optional[str] = None,
    remove_bookmarks: Optional[bool] = False,
):
    """Add bookmarks to a PDF from a table of contents

    Parameters
    ----------
    table_of_contents : List[str]
        The table of contents, an element per entry
    input_path : str
        The path to the original unbookmarked PDF
    output_path : str
        The path to write the bookmarked PDF to
    format : Optional[str] = "indents"
        Format to determine how the table of contents is broken into different levels
    print_tree : Optional[bool] = False
        Prints out the bookmark tree rather than add to PDF
    title : Optional[str] = None
        The title of the book to add into PDF metadata
    author : Optional[str] = None
        The author is the book to add into PDF metadata
    pdfmarks_save_path : Optional[str] = None
        The path to save the pdfmarks. If not supplied, a temp file will be created.
    remove_bookmarks : Optional[bool] = False
        Whether to strip bookmarks from the input PDF.
    """
    tree = parser.parse_table_of_contents(table_of_contents, format)

    if print_tree:
        parser.print_node_tree(tree)
        return

    page_numbers = pdfmarker.get_page_numbers(input_path)
    pdfmarks = pdfmarker.generate_pdfmarks(
        tree, page_numbers, title=title, author=author
    )

    file_context_manager = (
        open(pdfmarks_save_path, "w")
        if pdfmarks_save_path
        else tempfile.NamedTemporaryFile(mode="w")
    )
    with file_context_manager as fp:
        fp.write(pdfmarks)
        fp.flush()

        # Workaround hack for Gooey not supporting separate regexes for total
        # or current
        # see https://github.com/chriskiehl/Gooey/issues/547

        process = subprocess.Popen(
            filter(lambda x: x is not None, [
                "gs" if platform.system() != "Windows" else "gswin64",
                "-dBATCH",
                "-dNOPAUSE",
                "-dNO_PDFMARK_OUTLINES" if remove_bookmarks else None,
                "-sDEVICE=pdfwrite",
                "-sOutputFile={}".format(output_path),
                fp.name,
                input_path,
            ]),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        total = None
        for line in process.stdout:
            line = line.decode(sys.stdout.encoding)
            print(line, end="")
            if (m := re.match(r"^Processing pages 1 through (?P<total>\d+)\.$", line)) :
                total = m.group("total")
            elif (m := re.match(r"^Page (?P<current>\d+)$", line)) :
                if total is not None:
                    print(
                        "[progress]: {current}/{total}".format(
                            current=m.group("current"), total=total
                        )
                    )
                else:
                    raise Exception("This should not have happened")

        # subprocess.run(
        # [
        # "gs" if platform.system() != "Windows" else "gswin64",
        # "-dBATCH",
        # "-dNOPAUSE",
        # "-sDEVICE=pdfwrite",
        # "-sOutputFile={}".format(output_path),
        # fp.name,
        # input_path,
        # ],
        # check=True,
        # )


if __name__ == "__main__":
    arguments = parse_arguments()
    main(*arguments)
