# Define a base exception class for custom errors.
class BaseCustomException(Exception):
    # Error message and error code are defined for each custom exception.
    code: int

    def __init__(self, message: str):
        self.message = message


class BadRequestException(BaseCustomException):
    code: int = 400

    def __init__(self, message: str):
        self.message = message
