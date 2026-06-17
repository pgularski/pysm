import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def _load_script(name):
    path = ROOT / '.github' / 'scripts' / name
    spec = importlib.util.spec_from_file_location(name[:-3], str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prepend_changelog_entry_uses_project_heading_style():
    prepend = _load_script('prepend_changelog_entry.py')
    metadata = {
        'title': 'Fix optional module compatibility',
        'number': 29,
        'html_url': 'https://github.com/pgularski/pysm/pull/29',
        'labels': [{'name': 'Fixed'}],
        'user': {'login': 'pgularski'},
    }

    tag, entry, release_notes = prepend.build_entries(
        '0.4.1',
        '2026-06-17',
        metadata,
    )

    assert tag == '0.4.1'
    assert entry.startswith('## [0.4.1] - 2026-06-17')
    assert '### Fixed' in entry
    assert 'Fix optional module compatibility' in release_notes


def test_prepend_changelog_entry_does_not_duplicate_v_prefixed_heading():
    prepend = _load_script('prepend_changelog_entry.py')
    changelog = '# Changelog\n\n## [Unreleased]\n\n## [v0.4.1] - 2026-06-17\n'

    updated = prepend.insert_entry(changelog, '0.4.1', '## [0.4.1]\n')

    assert updated == changelog


def test_extract_changelog_entry_finds_recovery_release_notes():
    extract = _load_script('extract_changelog_entry.py')
    changelog = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')

    notes = extract.extract_entry(changelog, '0.4.1')

    assert 'MicroPython compatibility' in notes
    assert 'patch-release automation' in notes


def test_release_metadata_from_commit_builds_commit_fallback():
    metadata = _load_script('release_metadata_from_commit.py')

    data = metadata.build_metadata(
        'HEAD',
        'pgularski/pysm',
        'https://github.com/',
        'pgularski',
    )

    assert data['title'] == subprocess.check_output(
        ['git', 'log', '-1', '--pretty=%s', 'HEAD'],
        text=True,
    ).strip()
    assert data['html_url'].startswith(
        'https://github.com/pgularski/pysm/commit/')
    assert data['user'] == {'login': 'pgularski'}


def test_release_metadata_script_writes_json(tmp_path):
    output = tmp_path / 'metadata.json'

    subprocess.check_call([
        'python',
        str(ROOT / '.github' / 'scripts' / 'release_metadata_from_commit.py'),
        '--sha',
        'HEAD',
        '--repository',
        'pgularski/pysm',
        '--actor',
        'pgularski',
        '--output',
        str(output),
    ])

    data = json.loads(output.read_text(encoding='utf-8'))

    assert data['title']
    assert data['html_url'].endswith('/commit/HEAD')
