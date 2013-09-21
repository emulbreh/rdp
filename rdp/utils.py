import functools
import operator


def product(factors):
    return functools.reduce(operator.__mul__, factors, 1)


def uncurry(func):
    @functools.wraps(func)
    def uncurried(seq):
        return func(*seq)
    return uncurried

def chain(f, g):
    def chained(arg):
        return f(g(arg))
    return chained
