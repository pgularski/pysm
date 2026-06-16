from pathlib import Path
import argparse
import re


def normalize_version(version):
    version = version.strip()
    if version.startswith('v'):
        return version[1:]
    return version


def extract_entry(changelog, version):
    version = normalize_version(version)
    pattern = re.compile(
        r'^## \[v?{0}\][^\n]*\n(?P<body>.*?)(?=^## \[|\Z)'.format(
            re.escape(version)),
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(changelog)
    if not match:
        raise SystemExit('No changelog entry found for version {0}'.format(
            version))

    body = match.group('body').strip()
    if not body:
        raise SystemExit('Changelog entry for version {0} is empty'.format(
            version))
    return body + '\n'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', required=True)
    parser.add_argument('--changelog', type=Path, default=Path('CHANGELOG.md'))
    parser.add_argument('--output', type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    notes = extract_entry(
        args.changelog.read_text(encoding='utf-8'),
        args.version,
    )

    if args.output:
        args.output.write_text(notes, encoding='utf-8')
    else:
        print(notes, end='')


if __name__ == '__main__':
    main()
