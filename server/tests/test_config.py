import runpy
from pathlib import Path

import pytest

CONFIG = Path(__file__).resolve().parents[1] / "core" / "config.py"


def test_configuration_uses_environment(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "configured-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
    config = runpy.run_path(str(CONFIG))
    assert config["SECRET_KEY"] == "configured-key"
    assert config["DATABASE_URL"] == "postgresql+asyncpg://test:test@localhost/test"


@pytest.mark.parametrize("name", ["SECRET_KEY", "DATABASE_URL"])
@pytest.mark.parametrize("value", [None, "", "   "])
def test_required_configuration_rejects_missing_or_blank(monkeypatch, name, value):
    if value is None:
        monkeypatch.delenv(name, raising=False)
    else:
        monkeypatch.setenv(name, value)
    with pytest.raises(RuntimeError, match=name):
        runpy.run_path(str(CONFIG))
