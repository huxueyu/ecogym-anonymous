
import sys
from typing import TextIO


class FilteredStdout:

    def __init__(self, original_stdout: TextIO, filters: list = None):
        self.original_stdout = original_stdout
        self.filters = filters or [
            "<class 'agno.models.message.Message'>",
        ]
        self.buffer = ""
        self.filtering = False
        self.newline_count = 0

    def write(self, text: str) -> int:
        should_filter = False
        for filter_str in self.filters:
            if filter_str in text:
                should_filter = True
                self.filtering = True
                self.newline_count = 0
                break

        if self.filtering:
            if "\n" in text:
                self.newline_count += text.count("\n")
                if self.newline_count >= 2:
                    self.filtering = False
                    self.newline_count = 0
                    return len(text)
            return len(text)

        if should_filter:
            return len(text)

        return self.original_stdout.write(text)

    def flush(self):
        self.original_stdout.flush()

    def __getattr__(self, name):
        return getattr(self.original_stdout, name)


def install_stdout_filter():
    if not isinstance(sys.stdout, FilteredStdout):
        sys.stdout = FilteredStdout(sys.stdout)


def uninstall_stdout_filter():
    if isinstance(sys.stdout, FilteredStdout):
        sys.stdout = sys.stdout.original_stdout

