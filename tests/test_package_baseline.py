import importlib.metadata

import load_arena


def test_package_imports_and_version_matches_metadata():
    assert load_arena.__version__ == importlib.metadata.version("load_arena")
