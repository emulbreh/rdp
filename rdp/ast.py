

class Node(object):
    def __init__(self, symbol, value=None):
        self.symbol = symbol
        self.value = value
        self.children = []
        
    def append(self, node):
        if node.symbol.drop:
            return
        if node.symbol.flatten:
            for child in node.children:
                self.append(child)
        else:
            self.children.append(node)
            
    def __bool__(self):
        return bool(self.value or self.children)

    def __repr__(self):
        name = '{0}='.format(self.symbol.name) if self.symbol.name else ''
        return '<{0} {1}{2}>'.format(self.__class__.__name__, name, repr(self.value))
    
    def print_tree(self, indent=0):
        print('{0}{1}, lexeme={2}'.format(4 * indent * ' ', self.symbol, repr(getattr(self.value, 'lexeme', ''))))
        for child in self.children:
            child.print_tree(indent=indent + 1)


class Transform(object):
    pass