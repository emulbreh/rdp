

class Node(object):
    def __init__(self, symbol, token=None):
        self.symbol = symbol
        self.token = token
        self.children = []
        self.parent = None
        self.offset = self.token.start.source_offset if self.token else None

    def append(self, node):
        if node.symbol is None or node.symbol.drop:
            return
        if node.symbol.flatten:
            for child in node.children:
                self.append(child)
        else:
            self.children.append(node)
            node.parent = self
            if self.offset is None:
                self.offset = node.offset
            else:
                self.offset = min(self.offset, node.offset)

    def remove(self, node):
        try:
            self.children.remove(node)
        except ValueError:
            pass

    def discard(self):
        if self.parent:
            self.parent.remove(self)

    def __bool__(self):
        return bool(self.token or self.children)

    def transform(self):
        return self.symbol.apply_transform(self)

    def __len__(self):
        return len(self.children)

    def __iter__(self):
        return iter(self.children)

    def __getitem__(self, index):
        return self.children[index]

    def __repr__(self):
        name = '{0}='.format(self.symbol.name) if self.symbol.name else ''
        return '<{0} {1}{2}>'.format(self.__class__.__name__, name, repr(self.token))

    def print_tree(self):
        # FIXME: try to use box drawing characters: ┕, ━, ┣, ┃
        def lines(node, indent):
            for i, child in enumerate(node):
                yield '{indent}|___ {symbol} ({lexeme})'.format(
                    indent=indent,
                    symbol=child.symbol,
                    lexeme=repr(getattr(child.token, 'lexeme', '')),
                )
                next_indent = '  ' if i == len(node) - 1 else '|  '
                yield from lines(child, indent + next_indent)
        print(str(self.symbol) + "\n" + "\n".join(lines(self, '')))
