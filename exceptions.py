class BadInputException(Exception):
    def __init__(self, message):
        super(BadInputException, self).__init__(message)
