from anytree import Node, RenderTree
from enum import Enum, auto
import re
from typing import List, Tuple


class LevelType(Enum):
    # Always at a level; header
    ABSOLUTE = auto()
    # relative to last header
    HEADER = auto()
    # relative to the last entry
    CHILD = auto()
    # leaf, no children allowed - abs
    LEAF = auto()


SPACES_PER_LEVEL = 4


def indents_find_level(line: str) -> Tuple[LevelType, int]:
    return LevelType.ABSOLUTE, (len(line) - len(line.lstrip())) // SPACES_PER_LEVEL



def regex_1_find_level(line: str) -> Tuple[LevelType, int]:
    if re.match(r"^(Part)\s", line):
        # This should always be top level
        return LevelType.ABSOLUTE, 0
    if re.match("^(Chapter|Appendix)\s", line):
        # This should always be next to the last header
        # 0 -> same level as last header
        # e.g.
        # |-Root
        # | |-Chapter
        # | |-Part
        # | | |- Appendix
        return LevelType.HEADER, 0
    elif (m := re.match(r"^((?:\w+\.)+)\w+\s", line)):
        # This is relative to the last child
        # 0 is same level, 1 is below
        # in the style of X.X (so 1 -> child)
        return LevelType.CHILD, (m.group(1).count("."))

    else:
        # Index, Glossary, or Preface
        return LevelType.LEAF, 0


STYLES = {
    "indents": indents_find_level,
    "regex-1": regex_1_find_level,
}


def get_valid_styles() -> List[str]:
    return list(STYLES.keys())


def find_level(line: str, style: str) -> Tuple[LevelType, int]:
    """Returns the level the line should be on."""
    return STYLES[style](line)


def parse_entry(line: str, parent=None) -> Node:
    line_parts = line.split()
    header_name = " ".join(line_parts[:-1])
    page_number = line_parts[-1]

    return Node(header_name, page=page_number, parent=parent)


def parse_table_of_contents(table_of_contents: List[str], style: str) -> Node:
    root = Node("root", page=None)

    levels = {-1: root}
    last_header = 0

    for entry in table_of_contents:
        if entry:
            level_type, level = find_level(entry, style)
            
            if level_type == LevelType.ABSOLUTE:
                levels[level] = parse_entry(entry, parent=levels[level - 1])
                last_header = level
                
            elif level_type == LevelType.HEADER:
                abs_level = last_header + level
                levels[abs_level] = parse_entry(entry, parent=levels[abs_level - 1])
                last_header = last_child = abs_level
                
            elif level_type == LevelType.CHILD:
                abs_level = last_header + level
                levels[abs_level] = parse_entry(entry, parent=levels[abs_level - 1])
                last_child = abs_level
                
            elif level_type == LevelType.LEAF:
                parse_entry(entry, parent=levels[level - 1])
                last_header = last_child = 0

    return root


def print_node_tree(root_node: Node):
    for pre, fill, node in RenderTree(root_node):
        print("{}{} ({})".format(pre, node.name, node.page))
