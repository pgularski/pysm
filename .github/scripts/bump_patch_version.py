from pathlib import Path
import sys


def bump_patch_version(path):
    namespace = {}
    exec(path.read_text(encoding='utf-8'), namespace)

    version_info = namespace.get('__version_info__')
    if not isinstance(version_info, tuple) or len(version_info) != 3:
        raise SystemExit('Expected __version_info__ to be a 3-item tuple')

    major, minor, patch = version_info
    try:
        patch = int(patch)
    except (TypeError, ValueError):
        raise SystemExit('Expected patch version to be an integer string')

    new_version_info = (str(major), str(minor), str(patch + 1))
    path.write_text(
        "__version_info__ = {0!r}\n"
        "__version__ = '.'.join(__version_info__)\n".format(
            new_version_info),
        encoding='utf-8')
    return '.'.join(new_version_info)


if __name__ == '__main__':
    version_path = Path(sys.argv[1] if len(sys.argv) > 1
                        else 'pysm/version.py')
    print(bump_patch_version(version_path))
