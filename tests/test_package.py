from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_package_is_importable() -> None:
    import habits

    assert habits.__name__ == "habits"


def test_gitignore_ignores_python_and_pytest_caches() -> None:
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "__pycache__/" in lines
    assert ".pytest_cache/" in lines
