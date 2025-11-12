from enum import Enum


class AppEnv(str, Enum):
    """
    AppEnv is an enumeration that defines the different environments
    in which the application can run.
    """

    PRODUCTION = "production"  # Production environment for running application post build.
    DEVELOPMENT = "development"  # Development environment for local dev and debugging.
    TESTING = "testing"  # Testing environment for running test cases.
