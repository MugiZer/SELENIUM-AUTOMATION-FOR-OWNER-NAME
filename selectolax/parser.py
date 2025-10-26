from __future__ import annotations

from html.parser import HTMLParser as _HTMLParser
from typing import Callable, List, Optional, Tuple


class _Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text_parts")

    def __init__(self, tag: str, attrs: dict[str, str], parent: Optional["_Node"]) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: List[_Node] = []
        self.text_parts: List[str] = []

    def add_child(self, child: "_Node") -> None:
        self.children.append(child)

    def add_text(self, data: str) -> None:
        if data:
            self.text_parts.append(data)

    def iter_descendants(self):
        for child in self.children:
            yield child
            yield from child.iter_descendants()

    def sibling_index(self) -> int:
        if not self.parent:
            return 1
        try:
            return self.parent.children.index(self) + 1
        except ValueError:
            return 1


class _TreeBuilder(_HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.root = _Node("document", {}, None)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        attrs_dict = {name: value for name, value in attrs}
        parent = self.stack[-1]
        node = _Node(tag, attrs_dict, parent)
        parent.add_child(node)
        self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.stack:
            self.stack[-1].add_text(data)


class NodeWrapper:
    def __init__(self, node: _Node):
        self._node = node

    @property
    def tag(self) -> str:
        return self._node.tag

    @property
    def attrs(self) -> dict[str, str]:
        return self._node.attrs

    @property
    def parent(self) -> Optional["NodeWrapper"]:
        if self._node.parent:
            return NodeWrapper(self._node.parent)
        return None

    @property
    def next(self) -> Optional["NodeWrapper"]:
        if not self._node.parent:
            return None
        siblings = self._node.parent.children
        try:
            index = siblings.index(self._node)
        except ValueError:
            return None
        if index + 1 < len(siblings):
            return NodeWrapper(siblings[index + 1])
        return None

    def text(self) -> str:
        return "".join(self._collect_text(self._node)).strip()

    def _collect_text(self, node: _Node) -> List[str]:
        parts = list(node.text_parts)
        for child in node.children:
            parts.extend(self._collect_text(child))
        return parts

    def css(self, selector: str) -> List["NodeWrapper"]:
        return _css_select(self._node, selector)

    def css_first(self, selector: str) -> Optional["NodeWrapper"]:
        results = self.css(selector)
        return results[0] if results else None


class HTMLParser:
    def __init__(self, html: str) -> None:
        parser = _TreeBuilder()
        parser.feed(html)
        self.root = parser.root

    def css(self, selector: str) -> List[NodeWrapper]:
        return _css_select(self.root, selector)

    def css_first(self, selector: str) -> Optional[NodeWrapper]:
        results = self.css(selector)
        return results[0] if results else None


def _css_select(node: _Node, selector: str) -> List[NodeWrapper]:
    selectors = [_parse_selector(part.strip()) for part in selector.split(",") if part.strip()]
    results: List[_Node] = []
    for sel in selectors:
        results.extend(_select_single(node, sel))
    return [NodeWrapper(n) for n in results]


def _select_single(root: _Node, selector: List[Tuple[str, Callable[[_Node], bool]]]) -> List[_Node]:
    current = [root]
    for combinator, predicate in selector:
        next_nodes: List[_Node] = []
        for node in current:
            if combinator == ">":
                for child in node.children:
                    if predicate(child):
                        next_nodes.append(child)
            else:
                for descendant in node.iter_descendants():
                    if predicate(descendant):
                        next_nodes.append(descendant)
        current = next_nodes
    return current


def _parse_selector(selector: str) -> List[Tuple[str, Callable[[_Node], bool]]]:
    tokens: List[Tuple[str, Callable[[_Node], bool]]] = []
    buffer = ""
    combinator = None
    i = 0
    while i < len(selector):
        char = selector[i]
        if char == ">":
            if buffer.strip():
                tokens.append((combinator or " ", _compile_simple_selector(buffer.strip())))
                buffer = ""
            combinator = ">"
            i += 1
            continue
        if char.isspace():
            if buffer.strip():
                tokens.append((combinator or " ", _compile_simple_selector(buffer.strip())))
                buffer = ""
            combinator = " "
            while i < len(selector) and selector[i].isspace():
                i += 1
            continue
        buffer += char
        i += 1
    if buffer.strip():
        tokens.append((combinator or " ", _compile_simple_selector(buffer.strip())))
    if tokens:
        first_combinator, predicate = tokens[0]
        if first_combinator != ">":
            tokens[0] = ("descendant", predicate)
    return tokens


def _compile_simple_selector(selector: str) -> Callable[[_Node], bool]:
    tag = None
    classes: List[str] = []
    element_id = None
    nth_child: Optional[int] = None
    remainder = selector
    while remainder:
        if remainder.startswith(":nth-child("):
            end = remainder.find(")")
            if end != -1:
                nth_value = remainder[len(":nth-child(") : end]
                try:
                    nth_child = int(nth_value)
                except ValueError:
                    nth_child = None
                remainder = remainder[end + 1 :]
                continue
        if remainder.startswith("."):
            remainder = remainder[1:]
            name, remainder = _read_identifier(remainder)
            classes.append(name)
            continue
        if remainder.startswith("#"):
            remainder = remainder[1:]
            name, remainder = _read_identifier(remainder)
            element_id = name
            continue
        name, remainder = _read_identifier(remainder)
        if name:
            tag = name
    def predicate(node: _Node) -> bool:
        if tag and node.tag != tag:
            return False
        if element_id and node.attrs.get("id") != element_id:
            return False
        if classes:
            class_attr = node.attrs.get("class", "")
            node_classes = set(class_attr.split())
            if not all(cls in node_classes for cls in classes):
                return False
        if nth_child is not None and node.sibling_index() != nth_child:
            return False
        return True
    return predicate


def _read_identifier(text: str) -> Tuple[str, str]:
    i = 0
    while i < len(text) and text[i] not in ".#:( ":
        i += 1
    return text[:i], text[i:]
