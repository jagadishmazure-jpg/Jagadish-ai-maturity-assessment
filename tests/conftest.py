import shutil

import pytest

from aimaturity import SAMPLES
from aimaturity.agents.assessor import assess


@pytest.fixture(scope="session")
def portfolio():
    return assess("portfolio")


@pytest.fixture(scope="session")
def bank():
    return assess("kestrel-bay-bank")


@pytest.fixture(scope="session")
def agency():
    return assess("valemont-revenue-agency")


@pytest.fixture
def org_copy(tmp_path, monkeypatch):
    """A writable copy of a sample org so review tests never touch the checked-in files."""

    def make(org_id: str):
        dst = tmp_path / "samples"
        shutil.copytree(SAMPLES / org_id, dst / org_id)
        monkeypatch.setattr("aimaturity.orgs.SAMPLES", dst)
        return dst / org_id

    return make
