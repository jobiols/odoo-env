_instances = {}


class Singleton:
    def __new__(cls, *args, **kw):
        if cls not in _instances:
            instance = super().__new__(cls)
            _instances[cls] = instance
        return _instances[cls]
