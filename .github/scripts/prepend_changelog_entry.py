from datetime import date
import argparse
import json
import re
from pathlib import Path


DEFAULT_CHANGELOG = """# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
"""

CATEGORY_RULES = (
    ('Security', ('security',)),
    ('Removed', ('removed', 'removal')),
    ('Deprecated', ('deprecated', 'deprecation')),
    ('Added', ('added', 'feature', 'enhancement')),
    ('Fixed', ('fixed', 'fix', 'bug')),
    ('Documentation', ('documentation', 'docs')),
    ('Tests', ('test', 'tests')),
    ('CI', ('ci', 'github-actions', 'github actions')),
)


def normalize_label(label):
    return str(label).strip().lower()


def choose_category(labels):
    normalized = [normalize_label(label) for label in labels]
    for category, aliases in CATEGORY_RULES:
        for label in normalized:
            if label in aliases:
                return category
            if any(label.startswith(alias + ':') for alias in aliases):
                return category
    return 'Changed'


def collapse_whitespace(value):
    if value is None:
        return ''
    return ' '.join(str(value).split())


def build_bullet(metadata):
    title = collapse_whitespace(metadata.get('title')) or 'Merged pull request'
    number = metadata.get('number')
    url = metadata.get('html_url')
    user = metadata.get('user') or {}
    author = user.get('login')

    pieces = [title]
    if number and url:
        pieces.append('([#{0}]({1}))'.format(number, url))
    elif number:
        pieces.append('(#{0})'.format(number))
    if author:
        pieces.append('by @{0}'.format(author))

    return '- {0}'.format(' '.join(pieces))


def build_entries(version, release_date, metadata):
    tag = 'v{0}'.format(version)
    labels = [label.get('name', '') for label in metadata.get('labels') or []]
    category = choose_category(labels)
    bullet = build_bullet(metadata)
    changelog_entry = (
        '## [{tag}] - {release_date}\n\n'
        '### {category}\n\n'
        '{bullet}\n'
    ).format(
        tag=tag,
        release_date=release_date,
        category=category,
        bullet=bullet,
    )
    release_notes = '### {0}\n\n{1}\n'.format(category, bullet)
    return tag, changelog_entry, release_notes


def insert_entry(changelog, tag, entry):
    if re.search(r'^## \[{0}\](?:\s|-|\n)'.format(re.escape(tag)),
                 changelog, re.MULTILINE):
        return changelog

    if not changelog.strip():
        changelog = DEFAULT_CHANGELOG
    if not changelog.endswith('\n'):
        changelog += '\n'

    unreleased = re.search(r'^## \[Unreleased\]\s*$',
                           changelog, re.MULTILINE)
    if unreleased:
        following = changelog[unreleased.end():]
        next_heading = re.search(r'^## \[', following, re.MULTILINE)
        insert_at = (
            unreleased.end() + next_heading.start()
            if next_heading else len(changelog)
        )
    else:
        first_release = re.search(r'^## \[', changelog, re.MULTILINE)
        insert_at = first_release.start() if first_release else len(changelog)

    before = changelog[:insert_at].rstrip()
    after = changelog[insert_at:].lstrip('\n')
    if after:
        return '{0}\n\n{1}\n{2}'.format(before, entry.rstrip(), after)
    return '{0}\n\n{1}\n'.format(before, entry.rstrip())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', required=True)
    parser.add_argument('--date', default=date.today().isoformat())
    parser.add_argument('--pr-json', type=Path, required=True)
    parser.add_argument('--changelog', type=Path, default=Path('CHANGELOG.md'))
    parser.add_argument('--notes-file', type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    metadata = json.loads(args.pr_json.read_text(encoding='utf-8'))
    tag, changelog_entry, release_notes = build_entries(
        args.version,
        args.date,
        metadata,
    )

    changelog = (
        args.changelog.read_text(encoding='utf-8')
        if args.changelog.exists() else DEFAULT_CHANGELOG
    )
    args.changelog.write_text(
        insert_entry(changelog, tag, changelog_entry),
        encoding='utf-8',
    )

    if args.notes_file:
        args.notes_file.write_text(release_notes, encoding='utf-8')

    print(release_notes, end='')


if __name__ == '__main__':
    main()
