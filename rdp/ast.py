

class Node(object):
    def __init__(self, symbol, value=None):
        self.symbol = symbol
        self.value = value
        self.children = []
        self.offset = value.offset if value else None
        self.parent = None

    def append(self, node):
        if node.symbol.drop or not node:
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
        return bool(self.value or self.children)

    def __len__(self):
        return len(self.children)

    def __iter__(self):
        return iter(self.children)

    def __repr__(self):
        name = '{0}='.format(self.symbol.name) if self.symbol.name else ''
        return '<{0} {1}{2}>'.format(self.__class__.__name__, name, repr(self.value))

    def print_tree(self, indent=0):
        print('{0}{1}, lexeme={2}'.format(4 * indent * ' ', self.symbol, repr(getattr(self.value, 'lexeme', ''))))
        for child in self.children:
            child.print_tree(indent=indent + 1)


class Transform(object):
    pass