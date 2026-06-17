from pathlib import Path
import sys

import yaml


def workflow_paths(root):
    workflows = root / '.github' / 'workflows'
    return sorted(list(workflows.glob('*.yml')) + list(workflows.glob('*.yaml')))


def main():
    root = Path(__file__).resolve().parents[2]
    failed = False
    for path in workflow_paths(root):
        try:
            with path.open(encoding='utf-8') as handle:
                yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            print('{0}: {1}'.format(path, exc), file=sys.stderr)
            failed = True

    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
