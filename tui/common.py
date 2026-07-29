"""Shared types used by the platform runners and the TUI."""

from collections.abc import Callable
from dataclasses import dataclass


# ``arg`` describes how a collector is called:
#   "base"     -> fn(target, cfg)
#   "collabs"  -> fn(target, cfg, repo_collabs)   (GitHub collaborator cache)
#   "projects" -> fn(target, cfg, projects)       (GitLab project cache)
@dataclass(frozen=True)
class Check:
    key: str
    label: str
    fn: Callable
    filename: str
    arg: str = "base"
    note: str = ""


# kind is one of: "fetch", "start", "done", "error", "summary".
@dataclass(frozen=True)
class ProgressEvent:
    kind: str
    label: str
    count: int | None = None
    message: str = ""


ProgressCallback = Callable[[ProgressEvent], None]
