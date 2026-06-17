from pathlib import Path
import argparse
import json
import os
import subprocess


def commit_subject(sha):
    return subprocess.check_output(
        ['git', 'log', '-1', '--pretty=%s', sha],
        text=True,
    ).strip()


def build_metadata(sha, repository, server_url, actor):
    title = commit_subject(sha)
    return {
        'title': title or 'Merged package changes',
        'number': None,
        'html_url': '{0}/{1}/commit/{2}'.format(
            server_url.rstrip('/'),
            repository,
            sha,
        ),
        'labels': [],
        'user': {'login': actor},
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sha', default=os.environ.get('GITHUB_SHA', 'HEAD'))
    parser.add_argument(
        '--repository',
        default=os.environ.get('GITHUB_REPOSITORY', ''),
    )
    parser.add_argument(
        '--server-url',
        default=os.environ.get('GITHUB_SERVER_URL', 'https://github.com'),
    )
    parser.add_argument('--actor', default=os.environ.get('GITHUB_ACTOR', ''))
    parser.add_argument('--output', type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    metadata = build_metadata(
        args.sha,
        args.repository,
        args.server_url,
        args.actor,
    )
    args.output.write_text(json.dumps(metadata), encoding='utf-8')


if __name__ == '__main__':
    main()
