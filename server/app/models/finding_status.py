import enum

class FindingStatus(enum.Enum):
    open = "open"
    resolved = "resolved"
    dismissed = "dismissed"
    in_progress = "in_progress"

