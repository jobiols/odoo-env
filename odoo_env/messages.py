import sys

RED = "\033[1;31m"
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

    def run(self, msg):
        print(self.yellow(msg))

    def done(self, msg):
        print(self.green(msg))

    def err(self, msg):
        print(self.red(msg))
        sys.exit()

    def inf(self, msg):
        if msg:
            print(self.yellow_light(msg))

    def warn(self, msg):
        print(self.red(msg))
