from anytree import Node, RenderTree
import re
import argparse
from typing import List, Tuple, Optional
import os
import tempfile
import subprocess
import parser
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


def parse_arguments() -> Tuple[List[str], str, str]:
    main_parser = argparse.ArgumentParser(
        description="Add bookmarks to a PDF from a table of contents"
    )
    main_parser.add_argument(
        "table_of_contents",
        help="The path to the table of contents text file",
        type=file_contents,
    )
    main_parser.add_argument(
        "input_path", help="The original unbookmarked PDF", type=is_valid_file
    )
    main_parser.add_argument(
        "output_path",
        help="The path to write the bookmarked PDF to",
    )
    main_parser.add_argument("--title", help="The book title", default=None)
    main_parser.add_argument("--author", help="The book author", default=None)
    main_parser.add_argument(
        "-t",
        "--toc_delimiter",
        help="What to split the table of contents file by (default: \\n)",
        default="\n",
    )
    main_parser.add_argument(
        "-s",
        "--style",
        help="Format to determine how the table of contents is broken into different levels",
        default="indents",
        choices=parser.get_valid_styles(),
    )
    main_parser.add_argument(
        "-p",
        "--print_tree",
        help="Prints out the bookmark tree rather than add to PDF",
        action="store_true",
        default=False,
    )

    args = main_parser.parse_args()
    return (
        args.table_of_contents.split(args.toc_delimiter),
        args.input_path,
        args.output_path,
        args.style,
        args.print_tree,
        args.title,
        args.author,
    )


def main(
    table_of_contents: List[str],
    input_path: str,
    output_path: str,
    style: Optional[str] = "indents",
    print_tree: Optional[bool] = False,
    title: Optional[str] = None,
    author: Optional[str] = None,
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
    style : Optional[str] = "indents"
        Format to determine how the table of contents is broken into different levels
    print_tree : Optional[bool] = False
        Prints out the bookmark tree rather than add to PDF
    title : Optional[str] = None
        The title of the book to add into PDF metadata
    author : Optional[str] = None
        The author is the book to add into PDF metadata
    """
    tree = parser.parse_table_of_contents(table_of_contents, style)

    if print_tree:
        parser.print_node_tree(tree)
        return

    page_numbers = pdfmarker.get_page_numbers(input_path)
    pdfmarks = pdfmarker.generate_pdfmarks(tree, page_numbers, title=title, author=author)

    with tempfile.NamedTemporaryFile(mode="w") as fp:
        fp.write(pdfmarks)

        subprocess.run(
            [
                "gs",
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=pdfwrite",
                "-sOutputFile={}".format(output_path),
                fp.name,
                input_path,
            ],
            check=True,
        )


if __name__ == "__main__":
    arguments = parse_arguments()
    main(*arguments)
