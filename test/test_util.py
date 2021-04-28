import os


def test_file(name) -> str:
    return os.path.join(os.path.dirname(__file__), 'resources', name)
