"""Headless smoke tests for the Textual app.

Drives the app through its screens with a Pilot, stubbing the network-bound
run_audit so no real GitHub calls are made. Uses asyncio.run so the suite does
not require the pytest-asyncio plugin.
"""

import asyncio

from textual.widgets import Button, Input

from tui import github_runner as gh
from tui.app import AuditApp, ChecksScreen, ConfigScreen, MenuScreen, RunScreen


def _run(coro):
    asyncio.run(coro)


def test_full_navigation(monkeypatch):
    def fake_run_audit(*, org, token, output_dir, branch, selected_keys, on_event):
        on_event(gh.ProgressEvent("start", "Member roster"))
        on_event(gh.ProgressEvent("done", "Member roster", count=3))
        on_event(gh.ProgressEvent("summary", output_dir, count=3))
        return [("Member roster", 3)]

    monkeypatch.setattr("tui.github_runner.run_audit", fake_run_audit)

    async def scenario():
        app = AuditApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, MenuScreen)

            await pilot.click("#github")
            await pilot.pause()
            assert isinstance(app.screen, ConfigScreen)

            app.screen.query_one("#org", Input).value = "acme"
            app.screen.query_one("#token", Input).value = "tok"
            await pilot.click("#continue")
            await pilot.pause()
            assert isinstance(app.screen, ChecksScreen)
            assert app.settings["org"] == "acme"

            await pilot.click("#run")
            await pilot.pause()
            assert isinstance(app.screen, RunScreen)

            await app.workers.wait_for_complete()
            await pilot.pause()

            # When the run finishes, the exit buttons become enabled.
            assert app.screen.query_one("#menu", Button).disabled is False
            assert app.screen.query_one("#quit", Button).disabled is False

    _run(scenario())


def test_config_requires_org_and_token(monkeypatch):
    # Make sure env vars don't pre-fill the fields for this test.
    monkeypatch.delenv("GITHUB_ORG", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    async def scenario():
        app = AuditApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.click("#github")
            await pilot.pause()
            # Continue with empty fields -> stays on ConfigScreen with an error.
            await pilot.click("#continue")
            await pilot.pause()
            assert isinstance(app.screen, ConfigScreen)
            error_text = str(app.screen.query_one("#form-error").render())
            assert "provide" in error_text.lower()

    _run(scenario())


def test_gitlab_is_enabled():
    async def scenario():
        app = AuditApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert app.screen.query_one("#gitlab", Button).disabled is False

    _run(scenario())


def test_gitlab_navigation(monkeypatch):
    monkeypatch.delenv("GITLAB_GROUP", raising=False)
    monkeypatch.delenv("GITLAB_TOKEN", raising=False)

    def fake_run_audit(*, group, token, base_url, output_dir, selected_keys, on_event):
        on_event(gh.ProgressEvent("done", "Group members", count=7))
        on_event(gh.ProgressEvent("summary", output_dir, count=7))
        return [("Group members", 7)]

    monkeypatch.setattr("tui.gitlab_runner.run_audit", fake_run_audit)

    async def scenario():
        app = AuditApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#gitlab")
            await pilot.pause()
            assert isinstance(app.screen, ConfigScreen)

            app.screen.query_one("#group", Input).value = "my-group"
            app.screen.query_one("#token", Input).value = "glpat-x"
            await pilot.click("#continue")
            await pilot.pause()
            assert isinstance(app.screen, ChecksScreen)
            assert app.settings["group"] == "my-group"
            # Self-hosted URL defaults to gitlab.com.
            assert app.settings["base_url"] == "https://gitlab.com/api/v4"

            await pilot.click("#run")
            await pilot.pause()
            assert isinstance(app.screen, RunScreen)
            assert "gitlab_audit_my-group" in app.screen.output_dir

            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.screen.query_one("#menu", Button).disabled is False

    _run(scenario())


def test_aws_navigation(monkeypatch):
    for var in ("AWS_PROFILE", "AWS_DEFAULT_REGION", "AWS_AUDIT_ACCOUNT"):
        monkeypatch.delenv(var, raising=False)

    def fake_run_audit(
        *, profile, region, account, output_dir, selected_keys, on_event
    ):
        on_event(gh.ProgressEvent("done", "IAM users", count=5))
        on_event(gh.ProgressEvent("summary", output_dir, count=5))
        return [("IAM users", 5)]

    monkeypatch.setattr("tui.aws_runner.run_audit", fake_run_audit)

    async def scenario():
        app = AuditApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#aws")
            await pilot.pause()
            assert isinstance(app.screen, ConfigScreen)

            # AWS has no required fields — continue with defaults (default chain).
            await pilot.click("#continue")
            await pilot.pause()
            assert isinstance(app.screen, ChecksScreen)
            assert app.settings["profile"] == ""

            await pilot.click("#run")
            await pilot.pause()
            assert isinstance(app.screen, RunScreen)
            # Empty profile renders as "default" in the folder name.
            assert "aws_audit_default" in app.screen.output_dir

            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.screen.query_one("#menu", Button).disabled is False

    _run(scenario())


def test_azure_is_coming_soon_and_ado_is_enabled():
    async def scenario():
        app = AuditApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            azure = app.screen.query_one("#azure", Button)
            assert azure.disabled is True
            assert "coming soon" in str(azure.label).lower()
            assert app.screen.query_one("#azure_devops", Button).disabled is False

    _run(scenario())


def test_azure_devops_navigation(monkeypatch):
    monkeypatch.delenv("AZDO_ORG", raising=False)
    monkeypatch.delenv("AZDO_PAT", raising=False)

    def fake_run_audit(*, org, pat, base_url, output_dir, selected_keys, on_event):
        on_event(gh.ProgressEvent("done", "Projects", count=4))
        on_event(gh.ProgressEvent("summary", output_dir, count=4))
        return [("Projects", 4)]

    monkeypatch.setattr("tui.azure_devops_runner.run_audit", fake_run_audit)

    async def scenario():
        app = AuditApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#azure_devops")
            await pilot.pause()
            assert isinstance(app.screen, ConfigScreen)

            app.screen.query_one("#org", Input).value = "acme"
            app.screen.query_one("#pat", Input).value = "pat123"
            await pilot.click("#continue")
            await pilot.pause()
            assert isinstance(app.screen, ChecksScreen)
            assert app.settings["org"] == "acme"
            assert app.settings["base_url"] == "https://dev.azure.com"

            await pilot.click("#run")
            await pilot.pause()
            assert isinstance(app.screen, RunScreen)
            assert "azure_devops_audit_acme" in app.screen.output_dir

            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.screen.query_one("#menu", Button).disabled is False

    _run(scenario())
