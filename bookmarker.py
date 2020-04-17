from anytree import Node, RenderTree
import re

one_dot_entry = re.compile(r"^\w+\.\w+\s")
two_dot_entry = re.compile(r"^\w+\.\w+\.\w+\s")



def adjust_page_number(pnum) -> int:
    try:
        return int(pnum) + 32
    except ValueError:
        rom_val = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500, 'm': 1000}
        int_val = 0
        for i in range(len(pnum)):
            if i > 0 and rom_val[pnum[i]] > rom_val[pnum[i - 1]]:
                int_val += rom_val[pnum[i]] - 2 * rom_val[pnum[i - 1]]
            else:
                int_val += rom_val[pnum[i]]
        return int_val
    

def parse_toc(toc: str):
    toc_lines = toc.splitlines()

    root = Node("root", page="0")
    header_types = ["Part",["Chapter", "Appendix"]]

    current_part = None
    current_chapter = None
    current_one_dot = None

    for line in toc_lines:
        line_parts = line.split()
        
        if len(line_parts) == 2: # Index 227
            header_type = None
        else:
            header_type = line_parts[0] # Chapter
        
        page_number = str(adjust_page_number(line_parts[-1])) # 17
        header_name = " ".join(line_parts[:-1]) # Chapter 1 Computers, People, and Programming
        
        
        if one_dot_entry.match(line):
            # is an entry with one dot, e.g. 1.2 Hello World
            current_one_dot = Node(header_name, page=page_number, parent=current_chapter)

        elif two_dot_entry.match(line):
            # is an entry with two dots, e.g. 1.2.3 YEET
            Node(header_name, page=page_number, parent=current_one_dot)
        else:
            # is a header, e.g. Chapter 1 Computers, People, and Programming 17
                
            if header_type in ["Chapter", "Appendix"]:
                # one lower level
                current_chapter = Node(header_name, page=page_number, parent=current_part or root)
            elif header_type == "Part":
                # highest level
                current_part = Node(header_name, page=page_number, parent=root)
            elif header_type is None:
                # highest level but not a tree top
                Node(header_name, page=page_number, parent=root)
    
    return root
                
def print_tree(root_node: Node):
    for pre, fill, node in RenderTree(root_node):
        print("{}{} ({})".format(pre, node.name, node.page))


start = """\
[ /Title (Programming Principles and Practice Using C++)
  /Author (Bjarne Stroustrup)

"""
single_style = """\
[ /Title ({name}) /Page {page} /OUT pdfmark
"""
sub_style = """\
[ /Count -{num_subs} /Title ({name}) /Page {page} /OUT pdfmark
"""

def create_pdf_marks(node: Node, output=None):
    output = output or [start]
    for node in node.children:
        output.append("  " * node.depth)
        if node.children:
            output.append(sub_style.format(num_subs=len(node.children),
                                           name=node.name,
                                           page=node.page))
            create_pdf_marks(node, output)
            output.append("\n")
        else:
            output.append(single_style.format(name=node.name,
                                               page=node.page))
    return "".join(output)
    

if __name__ == "__main__":
    with open("toc.txt") as f:
        toc = f.read()
    
    tree = parse_toc(toc)
    # print_tree(tree)
    with open("pdfmarks.ps", "w") as f:
        f.write(create_pdf_marks(tree))
    # gs -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -sOutputFile=out.pdf pdfmarks.ps input.pdf
