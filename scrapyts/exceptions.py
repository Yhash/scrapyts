class SuperError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

class DownloadError(SuperError):
    pass


class ParseError(SuperError):
    pass