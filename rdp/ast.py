

class Node(object):
    def __init__(self, symbol, offset, token=None):
        self.symbol = symbol
        self.offset = offset
        self.token = token
        self.children = []
        self.parent = None

    def append(self, node):
        if node.symbol is None or node.symbol.drop:
            return
        if node.symbol.flatten:
            for child in node.children:
                self.append(child)
        else:
            self.children.append(node)
            node.parent = self

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
        
    def __str__(self):
        if self.token:
            return '{0} {1}'.format(self.symbol, repr(self.token.lexeme))
        return str(self.symbol)

    def tuple_tree(self):
        if self.token:
            return (self.symbol.name, self.token.lexeme)
        return (self.symbol.name, [node.tuple_tree() for node in self])

    def print_tree(self):
        # FIXME: try to use box drawing characters: ┕, ━, ┣, ┃
        def lines(node, indent):
            for i, child in enumerate(node):
                yield '{0}|--- {1}'.format(indent, child)
                next_indent = '   ' if i == len(node) - 1 else '|  '
                yield from lines(child, indent + next_indent)
        print(str(self) + "\n" + "\n".join(lines(self, '')))
