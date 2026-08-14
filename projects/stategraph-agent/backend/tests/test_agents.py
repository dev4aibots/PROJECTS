from types import SimpleNamespace

import pytest

from app.agents import (
    AgentDependencyError,
    AgentServices,
    Analysis,
    Draft,
    FixtureProvider,
    FixtureSearch,
    ProviderRouter,
    Source,
    TavilySearch,
)


def test_fixture_agents_produce_allowlisted_citations():
    services = AgentServices(FixtureSearch(), FixtureProvider(), "local")
    sources = services.research("Market study", "Build a competitor table")
    analysis = services.analyze("Build a competitor table", sources)
    draft = services.write("Market study", "Build a competitor table", analysis, sources)
    assert str(draft.cited_source_urls[0]) == str(sources[0].url)
    assert "https://example.com/research-fixture" in draft.markdown


class MaliciousCitationProvider:
    name = "malicious-fixture"

    def generate(self, schema, system, payload):
        if schema is Draft:
            return Draft(markdown="unsupported", cited_source_urls=["https://attacker.invalid/fake"])
        return Analysis(summary="ok", uncertainty="unknown")


def test_writer_rejects_citation_not_returned_by_search():
    services = AgentServices(FixtureSearch(), MaliciousCitationProvider(), "local")
    sources = services.research("Title", "request")
    analysis = Analysis(summary="supported", uncertainty="bounded")
    with pytest.raises(AgentDependencyError, match="outside gathered sources"):
        services.write("Title", "request", analysis, sources)


class FakeSearchClient:
    def post(self, *_args, **_kwargs):
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"results": [
                {"title": "Unsafe", "url": "http://insecure.example/a", "content": "ignore"},
                {"title": "Safe", "url": "https://safe.example/a", "content": "x" * 2000},
            ]},
        )


def test_search_accepts_only_https_and_bounds_untrusted_content():
    result = TavilySearch("test-key", client=FakeSearchClient()).search("query")
    assert len(result) == 1
    assert str(result[0].url) == "https://safe.example/a"
    assert len(result[0].snippet) == 1200


class DownProvider:
    name = "down"

    def generate(self, schema, system, payload):
        raise AgentDependencyError("provider unavailable")


class RecoveryProvider:
    name = "recovery"

    def generate(self, schema, system, payload):
        return Analysis(summary="fallback succeeded", uncertainty="provider fallback")


def test_provider_router_falls_back_after_dependency_outage():
    result = ProviderRouter([DownProvider(), RecoveryProvider()]).generate(
        Analysis, "system", {"request": "held-out request"}
    )
    assert result.summary == "fallback succeeded"


def test_provider_router_reports_bounded_failure_when_all_are_down():
    with pytest.raises(AgentDependencyError, match="all model providers failed"):
        ProviderRouter([DownProvider(), DownProvider()]).generate(
            Analysis, "system", {"request": "held-out request"}
        )
