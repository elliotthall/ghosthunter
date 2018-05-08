
class HunterError(Exception):
    """Base class for exceptions in this package."""
    pass


class StartupError(HunterError):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
