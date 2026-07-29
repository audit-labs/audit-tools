"""
Platform descriptors that let the TUI drive any collector runner.

Each Platform declares its connection form (``fields``), its checks, and how to
compute the output directory and run the audit. The screens in app.py are
written against this interface, so adding a platform is data, not new UI.
"""

import os
from collections.abc import Callable
from dataclasses import dataclass, field

from tui import aws_runner, github_runner, gitlab_runner
from tui.common import Check


@dataclass(frozen=True)
class Field:
    """One input on the connection screen."""

    key: str
    label: str
    placeholder: str = ""
    default: str = ""
    password: bool = False
    required: bool = False
    env: str | None = None  # environment variable used to pre-fill the value


@dataclass(frozen=True)
class Platform:
    key: str
    label: str
    subject: Callable[
        [dict], str
    ]  # (settings) -> audit subject shown on the run screen
    fields: list[Field]
    checks: list[Check]
    default_selection: list[str]
    output_dir: Callable[[dict], str]  # (settings) -> path
    run: Callable[..., object]  # (settings, output_dir, selected_keys, on_event)
    enabled: bool = True
    note: str = field(default="")


# Shared connection fields reused across platforms.
_OUT_FIELD = Field("out", "Output directory", default="./output")


def _prefill(f: Field) -> str:
    if f.env:
        value = os.environ.get(f.env, "").strip()
        if value:
            return value
    return f.default


def _github_output_dir(s: dict) -> str:
    return github_runner.default_output_dir(s["out"], s["org"])


def _github_run(s: dict, output_dir, selected_keys, on_event):
    return github_runner.run_audit(
        org=s["org"],
        token=s["token"],
        output_dir=output_dir,
        branch=s["branch"],
        selected_keys=selected_keys,
        on_event=on_event,
    )


def _gitlab_output_dir(s: dict) -> str:
    return gitlab_runner.default_output_dir(s["out"], s["group"])


def _gitlab_run(s: dict, output_dir, selected_keys, on_event):
    return gitlab_runner.run_audit(
        group=s["group"],
        token=s["token"],
        base_url=s["base_url"],
        output_dir=output_dir,
        selected_keys=selected_keys,
        on_event=on_event,
    )


def _aws_output_dir(s: dict) -> str:
    return aws_runner.default_output_dir(s["out"], s["profile"])


def _aws_run(s: dict, output_dir, selected_keys, on_event):
    return aws_runner.run_audit(
        profile=s["profile"],
        region=s["region"],
        account=s["account"],
        output_dir=output_dir,
        selected_keys=selected_keys,
        on_event=on_event,
    )


GITHUB = Platform(
    key="github",
    label="GitHub",
    subject=lambda s: s["org"],
    fields=[
        Field("org", "Organization", "my-org", required=True, env="GITHUB_ORG"),
        Field(
            "token",
            "Personal access token",
            "ghp_… (read:org, repo)",
            password=True,
            required=True,
            env="GITHUB_TOKEN",
        ),
        _OUT_FIELD,
        Field("branch", "Branch (for commit history)", default="main"),
    ],
    checks=github_runner.CHECKS,
    default_selection=github_runner.DEFAULT_SELECTION,
    output_dir=_github_output_dir,
    run=_github_run,
)

GITLAB = Platform(
    key="gitlab",
    label="GitLab",
    subject=lambda s: s["group"],
    fields=[
        Field(
            "group",
            "Group ID or path",
            "e.g. 1234567 or my-group",
            required=True,
            env="GITLAB_GROUP",
        ),
        Field(
            "token",
            "Personal access token",
            "glpat-… (read_api)",
            password=True,
            required=True,
            env="GITLAB_TOKEN",
        ),
        Field(
            "base_url",
            "API base URL (self-hosted)",
            default="https://gitlab.com/api/v4",
            env="GITLAB_URL",
        ),
        _OUT_FIELD,
    ],
    checks=gitlab_runner.CHECKS,
    default_selection=gitlab_runner.DEFAULT_SELECTION,
    output_dir=_gitlab_output_dir,
    run=_gitlab_run,
)

AWS = Platform(
    key="aws",
    label="AWS",
    subject=lambda s: s["profile"] or "default",
    fields=[
        Field(
            "profile",
            "AWS profile",
            "default chain, or a named / SSO profile",
            env="AWS_PROFILE",
        ),
        Field("region", "Region", "e.g. us-east-1", env="AWS_DEFAULT_REGION"),
        Field(
            "account",
            "Account name (SSO check only)",
            "optional; defaults to current account",
            env="AWS_AUDIT_ACCOUNT",
        ),
        _OUT_FIELD,
    ],
    checks=aws_runner.CHECKS,
    default_selection=aws_runner.DEFAULT_SELECTION,
    output_dir=_aws_output_dir,
    run=_aws_run,
)

PLATFORMS = [GITHUB, GITLAB, AWS]


def prefill(f: Field) -> str:
    """Public accessor for a field's pre-filled value (env var or default)."""
    return _prefill(f)
