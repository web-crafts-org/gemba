"""Values typed on the command line: ISO dates."""

import datetime
import re

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def iso_date(text: str) -> datetime.date | None:
    """The date written as exactly `YYYY-MM-DD`, or None when the text is anything else."""
    if DATE_PATTERN.match(text):
        try:
            return datetime.date.fromisoformat(text)
        except ValueError:
            return None
    return None
