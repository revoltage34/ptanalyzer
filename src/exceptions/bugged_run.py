class BuggedRun(RuntimeError):
    """An exception indicating that a run has bugged out - it does not have
    enough information to convert to a relative run.

    If require_heist_start is set to True, the analyzer should look for a 'job start' line.
    Otherwise, the analyzer can assume that a new run started that aborted the old run."""
    def __init__(self, reasons: list[str]):
        self.reasons = reasons

    def __str__(self):
        reason_str = '\n'.join(self.reasons)
        return f'Bugged run detected, no stats will be displayed. Bugs found:\n{reason_str}\n'
