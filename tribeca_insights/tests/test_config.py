import types
from urllib.error import URLError

import pytest

import tribeca_insights.config as config


class FakeRobot:
    def __init__(self, delays=None, error=False):
        self.delays = delays or {}
        self.error = error
        self.url = None

    def set_url(self, url: str) -> None:
        self.url = url

    def read(self) -> None:
        if self.error:
            raise URLError("fail")

    def crawl_delay(self, ua: str):
        return self.delays.get(ua)


def test_get_crawl_delay_specific(monkeypatch):
    """Return crawl-delay from robots.txt for our user agent."""
    robot = FakeRobot({"tribeca-insights": 1.5})
    monkeypatch.setattr(config.robotparser, "RobotFileParser", lambda: robot)
    assert config.get_crawl_delay("https://example.com") == pytest.approx(1.5)


def test_get_crawl_delay_fallback(monkeypatch):
    """Fallback to '*' user agent delay when specific not set."""
    robot = FakeRobot({"*": 0.8})
    monkeypatch.setattr(config.robotparser, "RobotFileParser", lambda: robot)
    assert config.get_crawl_delay("https://example.com") == pytest.approx(0.8)


def test_get_crawl_delay_error(monkeypatch):
    """Return default delay when robots.txt cannot be read."""
    robot = FakeRobot(error=True)
    monkeypatch.setattr(config.robotparser, "RobotFileParser", lambda: robot)
    monkeypatch.setattr(config, "crawl_delay", 0.3)
    assert config.get_crawl_delay("https://example.com") == pytest.approx(0.3)
