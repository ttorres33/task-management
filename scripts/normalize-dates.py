#!/usr/bin/env python3
"""
CLI wrapper: normalize date formats in task frontmatter to YYYY-MM-DD.

Logic lives in normalize.py so it can be imported. See that module for the
supported date formats.
"""

from config import describe_root
from normalize import normalize_all, report


def main():
    print(describe_root())
    report(normalize_all())


if __name__ == '__main__':
    main()
