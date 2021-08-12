class RunAbort(Exception):
    """An exception indicating that a run has aborted.

    If require_heist_start is set to True, the analyzer should look for a 'job start' line.
    Otherwise, the analyzer can assume that a new run started that aborted the old run."""
    def __init__(self, *, require_heist_start: bool):
        self.require_heist_start = require_heist_start
