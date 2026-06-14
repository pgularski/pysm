import importlib
import sys


def test_core_import_does_not_load_optional_modules():
    for name in [
            'pysm.queued',
            'pysm.serialization',
            'pysm.builder',
    ]:
        sys.modules.pop(name, None)

    import pysm
    importlib.reload(pysm)

    assert 'pysm.queued' not in sys.modules
    assert 'pysm.serialization' not in sys.modules
    assert 'pysm.builder' not in sys.modules
