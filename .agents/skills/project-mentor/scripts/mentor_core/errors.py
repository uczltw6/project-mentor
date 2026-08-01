"""Domain errors and stable CLI exit codes."""


class MentorError(Exception):
    """Base class for expected, user-actionable failures."""

    exit_code = 2


class InvalidInputError(MentorError):
    """Input JSON or a domain value is invalid."""


class UnsupportedVersionError(InvalidInputError):
    """A future or otherwise unsupported schema version was supplied."""


class DuplicateIdError(InvalidInputError):
    """A supposedly unique identifier appears more than once."""


class RevisionConflictError(MentorError):
    """The caller's expected revision or file content is stale."""

    exit_code = 3


class IOSafetyError(MentorError):
    """An explicit file operation failed or violated a safety rule."""

    exit_code = 4


class EventConflictError(MentorError):
    """An event identifier was replayed with different content."""

    exit_code = 5
