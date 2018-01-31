"""exceptions.py"""
class RunTestsException(Exception):
    """base Exception class for project exceptions"""
    pass
class VirtualenvException(RunTestsException):
    """base Exception class for Virtualenv context manager"""
    pass
class FailedVirtualenvCreate(VirtualenvException):
    """unable to create a valid virtualenv for testing in"""
    pass
