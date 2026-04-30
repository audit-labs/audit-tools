"""
Collect commit history for all repos in an org.
"""

from .api import paginate


def commits(org, cfg, branch="main"):
    """
    Return commits across all repos. Each row includes repo, branch, sha,
    author, date, message (first line), and change counts.

    Skips repos where the branch doesn't exist.
    """
    repos = paginate(f"https://api.github.com/orgs/{org}/repos", cfg)
    rows = []

    for repo in repos:
        repo_name = repo["name"]
        try:
            repo_commits = paginate(
                f"https://api.github.com/repos/{org}/{repo_name}/commits",
                cfg,
                {"sha": branch},
            )
        except Exception:
            # Branch doesn't exist in this repo or other API error -- skip
            continue

        for c in repo_commits:
            commit = c.get("commit", {})
            author = commit.get("author", {})
            stats = c.get("stats", {})
            rows.append(
                {
                    "repo": repo_name,
                    "branch": branch,
                    "sha": c.get("sha", "")[:12],
                    "author_name": author.get("name", ""),
                    "author_email": author.get("email", ""),
                    "date": author.get("date", ""),
                    "message": commit.get("message", "").splitlines()[0],
                    "additions": stats.get("additions", ""),
                    "deletions": stats.get("deletions", ""),
                }
            )

    return rows
