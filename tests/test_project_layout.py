from pathlib import Path


def test_dockerfile_copies_python_runtime_modules():
    docker = Path("Dockerfile").read_text()
    assert "COPY bot.py replies.py storage.py message_policy.py" in docker


def test_entrypoint_has_low_memory_headless_mode():
    script = Path("deploy/entrypoint.sh").read_text()
    assert 'BROWSER_HEADLESS:-false' in script
    assert 'headless mode: no Xvfb' in script


def test_public_docs_link_reproducible_runner():
    readme = Path("README.md").read_text()
    assert "python -m pytest -q" in readme
    assert "python demo.py" in readme
