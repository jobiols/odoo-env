from typing import NoReturn

RED = "\033[1;31m"


class OeError(Exception):
    pass


GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
YELLOW_LIGHT = "\033[33m"
CLEAR = "\033[0;m"


class Msg:
    @staticmethod
    def green(string):
        return GREEN + string + CLEAR

    @staticmethod
    def yellow(string):
        return YELLOW + string + CLEAR

    @staticmethod
    def red(string):
        return RED + string + CLEAR

    @staticmethod
    def yellow_light(string):
        return YELLOW_LIGHT + string + CLEAR

    def run(self, text):
        print(self.yellow(text))

    def done(self, text):
        print(self.green(text))

    def err(self, text) -> NoReturn:
        print(self.red(text))
        raise OeError(text)

    def inf(self, text):
        if text:
            print(self.yellow_light(text))

    def warn(self, text):
        print(self.red(text))


msg = Msg()
