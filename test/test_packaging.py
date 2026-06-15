import importlib
import subprocess
import sys


def test_core_import_does_not_load_optional_modules():
    for name in [
            'pysm.aio',
            'pysm.queued',
            'pysm.serialization',
            'pysm.builder',
    ]:
        sys.modules.pop(name, None)

    import pysm
    importlib.reload(pysm)

    assert 'pysm.aio' not in sys.modules
    assert 'pysm.queued' not in sys.modules
    assert 'pysm.serialization' not in sys.modules
    assert 'pysm.builder' not in sys.modules


def test_core_import_does_not_load_optional_runtime_modules():
    script = """
import sys
import pysm
for name in ('asyncio', 'json', 'pysm.aio', 'pysm.queued',
             'pysm.serialization', 'pysm.builder'):
    print('{0}={1}'.format(name, name in sys.modules))
"""
    result = subprocess.run(
        [sys.executable, '-c', script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=True)

    loaded = dict(line.split('=') for line in result.stdout.splitlines())

    assert loaded == {
        'asyncio': 'False',
        'json': 'False',
        'pysm.aio': 'False',
        'pysm.queued': 'False',
        'pysm.serialization': 'False',
        'pysm.builder': 'False',
    }
