
class Source:
    def __init__(self, s):
        if hasattr(s, 'read'):
            s = s.read()
        self.buffer = s
        self.line_numbers = LineNumberTable(s)

    def __str__(self):
        return self.buffer


class LineNumberTable:
    def __init__(self, s):
        self.size = len(s)
        self.table = []
        start = 0
        while True:
            end = s.find('\n', start) + 1
            if not end:
                break
            self.table.append(range(start, end))
            start = end

    def get_line(self, offset):
        if not (0 <= offset < self.size):
            raise IndexError("offset outside source: {0}".format(offset))

        lo, hi = 0, len(self.table)
        index, line = -1, range(0)
        while lo < hi:
            index = (lo + hi) // 2
            line = self.table[index]
            if offset >= line.stop:
                lo = index
            elif offset < line.start:
                hi = index
            elif offset in line:
                return index, line
            else:
                assert False

    def __getitem__(self, offset):
        index, line = self.get_line(offset)
        return index + 1

