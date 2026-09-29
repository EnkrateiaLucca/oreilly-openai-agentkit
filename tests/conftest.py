"""Offline test isolation: never load local credentials or make network requests."""
import os
import socket

os.environ["PYTHON_DOTENV_DISABLED"] = "1"

import pytest

from course.config import Settings
from course.schemas import Citation, Claim, ResearchBrief


@pytest.fixture(autouse=True)
def offline_only(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("COURSE_USERS_JSON", raising=False)

    def no_network(*args, **kwargs):
        raise AssertionError("Tests must not contact external services.")

    monkeypatch.setattr(socket, "getaddrinfo", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)


@pytest.fixture
def settings():
    return Settings(model="test-model", input_rate=None, output_rate=None)


@pytest.fixture
def page_text():
    return "The study compares retrieval methods using a fixed evaluation dataset."


@pytest.fixture
def valid_brief(page_text):
    return ResearchBrief(
        title="A supported research brief",
        claims=[Claim(text="The study compares retrieval methods.", evidence=Citation(
            source_id="paper:1", quote=page_text))],
        not_found=[], limitations=["One supplied page only."], action="none",
    )
