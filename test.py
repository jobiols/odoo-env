# -*- coding: utf-8 -*-
# For copyright and license notices, see __manifest__.py file in module root


_instances = {}

class Singleton(object):

   def __new__(cls, *args, **kw):
      if not cls in _instances:
          instance = super(Singleton,cls).__new__(cls)
          _instances[cls] = instance

      return _instances[cls]


class MyClass(Singleton):
    """
    Example class.
    """

    pass


def main():
    m1 = MyClass()
    m2 = MyClass()
    assert m1 is m2


if __name__ == "__main__":
    main()