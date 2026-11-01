"""
fetch_github_data.py - Module to retrieve GitHub account data for the Profile Dashboard.
Handles authentication, rate limits, pagination, and multi-tier fallbacks.
"""

import os
import json
import base64
import urllib.request
import urllib.error
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "profile.json"
DATA_DIR = BASE_DIR / "data"

# Standard GitHub language color mappings
GITHUB_LANGUAGE_COLORS = {
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Dart": "#00b4ab",
    "Python": "#3572a5",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "C#": "#178600",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "SCSS": "#c6538c",
    "PHP": "#4F5D95",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Shell": "#89e051",
    "EJS": "#a91e50",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "Other": "#8b949e",
    "Lainnya": "#8b949e"
}

EXTENSION_TO_LANGUAGE = {
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".dart": "Dart",
    ".py": "Python",
    ".java": "Java",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".c": "C",
    ".h": "C",
    ".cs": "C#",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SCSS",
    ".php": "PHP",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".sh": "Shell",
    ".bash": "Shell",
    ".ejs": "EJS",
    ".vue": "Vue",
    ".svelte": "Svelte"
}

IGNORED_FILE_PATTERNS = [
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "composer.lock",
    "Cargo.lock",
    "Gemfile.lock",
    ".min.js",
    ".min.css",
    "node_modules/",
    "dist/",
    "build/",
    ".next/",
    "vendor/",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".rar",
    ".tar",
    ".gz"
]


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"username": "Zakkyaulia"}


def get_auth_token():
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or None


def github_request(url, is_json=True):
    token = get_auth_token()
    headers = {
        "User-Agent": "GitHub-Profile-Dashboard/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            if is_json:
                return json.loads(content.decode("utf-8"))
            return content
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for URL: {url}")
        return None
    except Exception as e:
        print(f"Request failed for {url}: {e}")
        return None


def fetch_avatar_base64(avatar_url):
    """Download avatar and convert to base64 data URL so SVG renders offline in GitHub Camo."""
    if not avatar_url:
        return None
    try:
        content = github_request(avatar_url, is_json=False)
        if content:
            # Determine mime type
            mime = "image/png"
            if avatar_url.endswith(".jpg") or avatar_url.endswith(".jpeg"):
                mime = "image/jpeg"
            elif avatar_url.endswith(".webp"):
                mime = "image/webp"
            b64_str = base64.b64encode(content).decode("utf-8")
            return f"data:{mime};base64,{b64_str}"
    except Exception as e:
        print(f"Failed to fetch avatar image: {e}")
    return None


def fetch_graphql_contributions(username, token):
    """Fetch contributions via GraphQL API if token is provided."""
    if not token:
        return None

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
                weekday
              }
            }
          }
        }
      }
    }
    """
    req_body = json.dumps({"query": query, "variables": {"login": username}}).encode("utf-8")
    headers = {
        "User-Agent": "GitHub-Profile-Dashboard/1.0",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request("https://api.github.com/graphql", data=req_body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            calendar = data.get("data", {}).get("user", {}).get("contributionsCollection", {}).get("contributionCalendar")
            return calendar
    except Exception as e:
        print(f"GraphQL request failed: {e}")
        return None


def fetch_public_contributions(username):
    """Fetch contributions using public calendar endpoints with multi-tier fallback."""
    # 1. Try jogruber contributions API
    try:
        url = f"https://github-contributions-api.jogruber.de/v4/{username}"
        req = urllib.request.Request(url, headers={"User-Agent": "GitHub-Profile-Dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and "contributions" in data:
                return data
    except Exception as e:
        print(f"jogruber API fallback failed: {e}")

    # 2. Try scraping GitHub public contribution HTML directly
    try:
        url = f"https://github.com/users/{username}/contributions"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")
            import re
            # Find all contribution days
            days = re.findall(r'<td[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"[^>]*>', html)
            if days:
                contributions_list = []
                for d, lvl in days:
                    # level 0-4
                    contributions_list.append({
                        "date": d,
                        "count": int(lvl) if int(lvl) > 0 else 0,
                        "level": int(lvl)
                    })
                return {
                    "total": {},
                    "contributions": contributions_list
                }
    except Exception as e:
        print(f"Direct HTML contributions scrape failed: {e}")

    return None


def fetch_all_data(config=None):
    if not config:
        config = load_config()

    username = config.get("username", "Zakkyaulia")
    token = get_auth_token()
    days_back = config.get("language_reporting_period_days", 90)
    cutoff_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_back)).isoformat()
    exclude_bots = set(config.get("exclude_bots", ["github-actions[bot]", "dependabot[bot]"]))

    print(f"Fetching GitHub data for {username} (Authenticated: {token is not None})...")

    # 1. User Profile
    user_data = github_request(f"https://api.github.com/users/{username}") or {}
    avatar_base64 = fetch_avatar_base64(user_data.get("avatar_url"))

    # 2. Public Repositories (sorted by pushed)
    repos = github_request(f"https://api.github.com/users/{username}/repos?sort=pushed&per_page=30") or []

    # 3. Commits & Language Lines Changed in the last 90 days
    # We want:
    # - Latest qualifying commit authored by user
    # - Lines added/changed per programming language
    latest_qualifying_commit = None
    language_line_counts = {}
    language_commit_counts = {}
    repo_language_stats = {}

    recent_active_repos = []
    for r in repos:
        pushed_at = r.get("pushed_at") or ""
        if pushed_at >= cutoff_date:
            recent_active_repos.append(r)

    print(f"Found {len(recent_active_repos)} active repositories in the last {days_back} days.")

    # Iterate through active repos to find commits
    for r in recent_active_repos:
        repo_name = r["name"]
        owner = r["owner"]["login"]
        commits_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits?author={username}&since={cutoff_date}&per_page=20"
        repo_commits = github_request(commits_url) or []

        for c in repo_commits:
            author_login = (c.get("author") or {}).get("login", "")
            committer_login = (c.get("committer") or {}).get("login", "")
            commit_author_name = c.get("commit", {}).get("author", {}).get("name", "")
            commit_date_str = c.get("commit", {}).get("author", {}).get("date")

            # Check bot exclusions
            if author_login in exclude_bots or committer_login in exclude_bots or commit_author_name in exclude_bots:
                continue

            # Check if this is the newest commit overall
            if commit_date_str:
                if not latest_qualifying_commit or commit_date_str > latest_qualifying_commit["date"]:
                    latest_qualifying_commit = {
                        "repo": repo_name,
                        "sha": c.get("sha", "")[:7],
                        "date": commit_date_str,
                        "message": c.get("commit", {}).get("message", "").split("\n")[0],
                        "author": commit_author_name or author_login
                    }

            # Fetch commit details for file changes (rate-limit safe)
            sha = c.get("sha")
            if sha:
                detail_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits/{sha}"
                detail = github_request(detail_url)
                if detail and "files" in detail:
                    for f in detail["files"]:
                        filename = f.get("filename", "")
                        # Check ignored patterns
                        if any(pat in filename for pat in IGNORED_FILE_PATTERNS):
                            continue

                        _, ext = os.path.splitext(filename.lower())
                        lang = EXTENSION_TO_LANGUAGE.get(ext)
                        if lang:
                            changes = f.get("changes", 0)
                            additions = f.get("additions", 0)
                            # Use additions + changes (or additions)
                            metric_val = additions if additions > 0 else changes
                            language_line_counts[lang] = language_line_counts.get(lang, 0) + metric_val
                            language_commit_counts[lang] = language_commit_counts.get(lang, 0) + 1

        # Also get repository fallback languages in case line counts are minimal or rate limited
        lang_url = f"https://api.github.com/repos/{owner}/{repo_name}/languages"
        repo_langs = github_request(lang_url) or {}
        repo_language_stats[repo_name] = repo_langs

    # If language_line_counts is empty (e.g. rate limit prevented commit detail), fallback to repo languages
    if not language_line_counts:
        print("Using repository language sizes as fallback for language distribution...")
        for repo_name, langs in repo_language_stats.items():
            for lang, size in langs.items():
                language_line_counts[lang] = language_line_counts.get(lang, 0) + size

    # 4. Public Events (Recent Activities)
    events = github_request(f"https://api.github.com/users/{username}/events/public?per_page=30") or []

    # 5. Contributions Data
    contributions_data = None
    if token:
        contributions_data = fetch_graphql_contributions(username, token)

    if not contributions_data:
        contributions_data = fetch_public_contributions(username)

    # Compile raw data package
    output_data = {
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "username": username,
        "user_profile": {
            "login": user_data.get("login", username),
            "name": user_data.get("name") or config.get("display_name", username),
            "bio": user_data.get("bio", ""),
            "avatar_url": user_data.get("avatar_url", ""),
            "avatar_base64": avatar_base64,
            "public_repos": user_data.get("public_repos", len(repos)),
            "created_at": user_data.get("created_at", "")
        },
        "latest_qualifying_commit": latest_qualifying_commit,
        "language_line_counts": language_line_counts,
        "language_commit_counts": language_commit_counts,
        "recent_repos": [
            {
                "name": r["name"],
                "language": r.get("language") or "Other",
                "pushed_at": r.get("pushed_at"),
                "updated_at": r.get("updated_at"),
                "stargazers_count": r.get("stargazers_count", 0),
                "fork": r.get("fork", False)
            } for r in repos[:10]
        ],
        "events": events[:20],
        "contributions_data": contributions_data
    }

    # Save to disk
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = DATA_DIR / "github_raw.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"Data saved successfully to {raw_path}")
    return output_data


if __name__ == "__main__":
    fetch_all_data()
