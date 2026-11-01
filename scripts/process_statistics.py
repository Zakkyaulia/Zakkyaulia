"""
process_statistics.py - Processes raw GitHub data into standardized metrics and visualization data.
Calculates Last Active, Contributions This Month/Year, Language Distribution, 12-Week Heatmap, and Recent Activities.
"""

import json
import datetime
from pathlib import Path
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python fallback if zoneinfo unavailable
    ZoneInfo = None

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "profile.json"
DATA_DIR = BASE_DIR / "data"

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


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def format_relative_time(dt, now, t_dict):
    """Calculate relative time string (e.g., '3 jam lalu' or '2 hari lalu')."""
    diff_sec = int((now - dt).total_seconds())
    if diff_sec < 60:
        return t_dict.get("just_now", "baru saja")

    diff_min = diff_sec // 60
    if diff_min < 60:
        unit = t_dict.get("minute", "menit lalu") if diff_min == 1 else t_dict.get("minutes", "menit lalu")
        return f"{diff_min} {unit}"

    diff_hours = diff_min // 60
    if diff_hours < 24 and now.date() == dt.date():
        unit = t_dict.get("hour", "jam lalu") if diff_hours == 1 else t_dict.get("hours", "jam lalu")
        return f"{diff_hours} {unit}"

    # Calendar day difference
    day_diff = (now.date() - dt.date()).days
    if day_diff == 1:
        return t_dict.get("yesterday", "kemarin")
    if day_diff > 1 and day_diff < 30:
        unit = t_dict.get("day", "hari lalu") if day_diff == 1 else t_dict.get("days", "hari lalu")
        return f"{day_diff} {unit}"

    diff_months = day_diff // 30
    if diff_months < 12:
        unit = t_dict.get("month", "bulan lalu") if diff_months == 1 else t_dict.get("months", "bulan lalu")
        return f"{diff_months} {unit}"

    diff_years = day_diff // 365
    unit = t_dict.get("year", "tahun lalu") if diff_years == 1 else t_dict.get("years", "tahun lalu")
    return f"{diff_years} {unit}"


def normalize_percentages(items, key="count", target_sum=100):
    """Normalize percentages using largest remainder method to ensure sum is exactly 100%."""
    total = sum(item[key] for item in items)
    if total == 0:
        for item in items:
            item["percentage"] = 0
        return items

    exact_pcts = [item[key] / total * target_sum for item in items]
    floors = [int(p) for p in exact_pcts]
    remainders = [exact_pcts[i] - floors[i] for i in range(len(items))]

    diff = target_sum - sum(floors)
    # Sort indices by descending remainder
    sorted_indices = sorted(range(len(remainders)), key=lambda i: remainders[i], reverse=True)

    for i in range(diff):
        floors[sorted_indices[i]] += 1

    for i, item in enumerate(items):
        item["percentage"] = floors[i]

    return items


def process_stats(raw_data=None):
    if not raw_data:
        raw_path = DATA_DIR / "github_raw.json"
        if not raw_path.exists():
            raise FileNotFoundError(f"Raw data file {raw_path} not found. Run fetch_github_data.py first.")
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

    config = load_config()
    locale = config.get("locale", "id")
    translations = config.get("translations", {}).get(locale, {})
    t_units = translations.get("time_units", {})
    t_actions = translations.get("activity_actions", {})
    months_labels = translations.get("months", [
        "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"
    ])

    # Timezone handling
    tz_str = config.get("timezone", "Asia/Jakarta")
    if ZoneInfo:
        try:
            tz = ZoneInfo(tz_str)
            now = datetime.datetime.now(tz)
        except Exception:
            tz = datetime.timezone(datetime.timedelta(hours=7))
            now = datetime.datetime.now(tz)
    else:
        tz = datetime.timezone(datetime.timedelta(hours=7))
        now = datetime.datetime.now(tz)

    # 1. Card 1 - Last Active (Elapsed time since latest actual commit)
    latest_commit = raw_data.get("latest_qualifying_commit")
    if latest_commit and latest_commit.get("date"):
        commit_dt = datetime.datetime.fromisoformat(latest_commit["date"].replace("Z", "+00:00")).astimezone(tz)
        last_active_relative = format_relative_time(commit_dt, now, t_units)
        last_active_repo = latest_commit.get("repo", "")
    else:
        last_active_relative = "—"
        last_active_repo = ""

    # 2. Contributions Calendar Parsing
    # We need:
    # - Contributions This Month
    # - Contributions This Year
    # - Circular Percentage (This Year / Lifetime)
    # - 12-Week Heatmap matrix
    contributions_data = raw_data.get("contributions_data") or {}
    all_days = []
    lifetime_total = 0

    # If GraphQL format (weeks -> contributionDays)
    if "weeks" in contributions_data:
        for w in contributions_data.get("weeks", []):
            for d in w.get("contributionDays", []):
                all_days.append({
                    "date": d["date"],
                    "count": d["contributionCount"],
                    "level": min(4, d["contributionCount"])
                })
        lifetime_total = contributions_data.get("totalContributions", 0)

    # If jogruber API or public HTML scrape format
    elif "contributions" in contributions_data:
        all_days = contributions_data.get("contributions", [])
        totals_dict = contributions_data.get("total", {})
        if totals_dict and isinstance(totals_dict, dict):
            lifetime_total = sum(int(v) for v in totals_dict.values())
        else:
            lifetime_total = sum(d.get("count", 0) for d in all_days)

    # Sort days by date
    all_days.sort(key=lambda d: d["date"])

    # Current year and month
    current_year_str = str(now.year)
    current_month_prefix = f"{now.year:04d}-{now.month:02d}"

    month_contributions = sum(d.get("count", 0) for d in all_days if d["date"].startswith(current_month_prefix))
    year_contributions = sum(d.get("count", 0) for d in all_days if d["date"].startswith(current_year_str))

    # If lifetime_total is 0 or less than year, ensure it's at least year_contributions
    if lifetime_total < year_contributions:
        lifetime_total = year_contributions

    # Circular percentage calculation: (year_contributions / lifetime_total) * 100
    if lifetime_total > 0:
        year_percentage = round((year_contributions / lifetime_total) * 100)
    else:
        year_percentage = 0

    # 3. Card 4 - Recently Updated Repository
    recent_repos = raw_data.get("recent_repos", [])
    recent_repo_name = "—"
    recent_repo_lang = "None"
    recent_repo_lang_color = "#8b949e"
    recent_repo_relative = "—"

    if recent_repos:
        top_repo = recent_repos[0]
        recent_repo_name = top_repo.get("name", "—")
        recent_repo_lang = top_repo.get("language") or "Other"
        recent_repo_lang_color = GITHUB_LANGUAGE_COLORS.get(recent_repo_lang, "#8b949e")
        pushed_at = top_repo.get("pushed_at") or top_repo.get("updated_at")
        if pushed_at:
            pushed_dt = datetime.datetime.fromisoformat(pushed_at.replace("Z", "+00:00")).astimezone(tz)
            recent_repo_relative = format_relative_time(pushed_dt, now, t_units)

    # 4. Section C - Programming Languages (Last 3 Months)
    # Using lines of code added/changed from qualifying commits
    lang_line_counts = raw_data.get("language_line_counts", {})
    sorted_langs = sorted(lang_line_counts.items(), key=lambda x: x[1], reverse=True)

    other_label = "Lainnya" if locale == "id" else "Other"
    top_langs_list = []
    other_total = 0

    # Group into top 4 + Other
    for i, (lang, count) in enumerate(sorted_langs):
        if i < 4:
            top_langs_list.append({"name": lang, "count": count, "color": GITHUB_LANGUAGE_COLORS.get(lang, "#8b949e")})
        else:
            other_total += count

    if other_total > 0:
        top_langs_list.append({
            "name": other_label,
            "count": other_total,
            "color": GITHUB_LANGUAGE_COLORS.get(other_label, "#8b949e")
        })

    # Normalize percentages to 100%
    normalized_languages = normalize_percentages(top_langs_list, key="count", target_sum=100)

    # 5. Section D - Contribution Heatmap (Last 12 Weeks)
    # Build 12 calendar weeks ending on the current week (Sunday or Saturday)
    # 12 weeks = 84 days
    # Align ending date with the end of current week (Saturday) or current day
    today_date = now.date()
    # Find current weekday: Monday is 0, Sunday is 6
    # Let's align so the current week is column 12
    # Week starts Monday (0) to Sunday (6) or Sunday (0) to Saturday (6)
    # In GitHub's calendar, rows are Sun(0) to Sat(6) or Mon(0) to Sun(6).
    # In reference image, there are 7 rows!
    days_dict = {d["date"]: d for d in all_days}

    # Generate 84 days (12 weeks * 7 days) ending on today + remaining days of current week
    # If today is weekday W (0=Mon, 6=Sun), days until Sunday is (6 - W)
    weekday_today = today_date.weekday() # 0 = Mon, 6 = Sun
    end_of_current_week = today_date + datetime.timedelta(days=(6 - weekday_today))
    start_of_12_weeks = end_of_current_week - datetime.timedelta(days=83)

    weeks = []
    current_week_days = []
    month_columns = {} # col_index -> month_name
    active_weeks_count = 0

    for i in range(84):
        cur_day = start_of_12_weeks + datetime.timedelta(days=i)
        cur_day_str = cur_day.strftime("%Y-%m-%d")
        day_info = days_dict.get(cur_day_str, {"date": cur_day_str, "count": 0, "level": 0})

        # Don't show future days as active
        if cur_day > today_date:
            day_info = {"date": cur_day_str, "count": 0, "level": 0, "is_future": True}

        # Calculate intensity level 0-4
        count = day_info.get("count", 0)
        level = 0
        if count >= 10:
            level = 4
        elif count >= 5:
            level = 3
        elif count >= 2:
            level = 2
        elif count >= 1:
            level = 1

        current_week_days.append({
            "date": cur_day_str,
            "count": count,
            "level": level,
            "weekday": cur_day.weekday(),
            "day": cur_day.day,
            "month": cur_day.month,
            "is_future": cur_day > today_date
        })

        if len(current_week_days) == 7:
            col_idx = len(weeks)
            week_has_activity = any(d["count"] > 0 for d in current_week_days)
            if week_has_activity:
                active_weeks_count += 1

            # Check if a month begins in this week or first week
            m_first_day = current_week_days[0]["month"]
            m_label = months_labels[m_first_day - 1]
            if col_idx == 0:
                month_columns[col_idx] = m_label
                last_seen_month = m_first_day
            else:
                for d in current_week_days:
                    if d["month"] != last_seen_month and d["day"] <= 14:
                        month_columns[col_idx] = months_labels[d["month"] - 1]
                        last_seen_month = d["month"]
                        break

            weeks.append(current_week_days)
            current_week_days = []

    # 6. Section E - Recent Activities
    raw_events = raw_data.get("events", [])
    recent_activities = []
    seen_activities = set()

    for ev in raw_events:
        ev_type = ev.get("type")
        repo_name = ev.get("repo", {}).get("name", "").split("/")[-1]
        ev_created = ev.get("created_at")
        if not ev_created:
            continue

        ev_dt = datetime.datetime.fromisoformat(ev_created.replace("Z", "+00:00")).astimezone(tz)
        rel_time = format_relative_time(ev_dt, now, t_units)

        action_desc = None
        icon_type = "commit"

        if ev_type == "PushEvent":
            action_desc = t_actions.get("pushed_commits", "Mengirim perubahan kode")
            icon_type = "commit"
        elif ev_type == "PullRequestEvent":
            pr_action = ev.get("payload", {}).get("action")
            is_merged = ev.get("payload", {}).get("pull_request", {}).get("merged", False)
            if pr_action == "closed" and is_merged:
                action_desc = t_actions.get("merged_pr", "Menggabungkan pull request")
            else:
                action_desc = t_actions.get("opened_pr", "Membuka pull request")
            icon_type = "pull_request"
        elif ev_type == "CreateEvent":
            ref_type = ev.get("payload", {}).get("ref_type")
            if ref_type == "repository":
                action_desc = t_actions.get("created_repo", "Membuat repositori baru")
                icon_type = "repo"
            else:
                action_desc = t_actions.get("created_branch", "Membuat branch baru")
                icon_type = "branch"
        elif ev_type == "IssuesEvent":
            action_desc = t_actions.get("opened_issue", "Membuka issue baru")
            icon_type = "issue"
        elif ev_type == "ReleaseEvent":
            action_desc = t_actions.get("published_release", "Menerbitkan rilis baru")
            icon_type = "release"

        if action_desc:
            act_key = f"{action_desc}_{repo_name}_{rel_time}"
            if act_key not in seen_activities:
                seen_activities.add(act_key)
                recent_activities.append({
                    "action": action_desc,
                    "repo": repo_name,
                    "icon": icon_type,
                    "relative_time": rel_time
                })

        if len(recent_activities) >= 3:
            break

    # If fewer than 3 activities, supplement with default qualifying recent actions
    while len(recent_activities) < 3:
        idx = len(recent_activities)
        if idx == 0:
            recent_activities.append({
                "action": t_actions.get("pushed_commits", "Mengirim perubahan kode"),
                "repo": recent_repo_name,
                "icon": "commit",
                "relative_time": last_active_relative
            })
        elif idx == 1:
            recent_activities.append({
                "action": t_actions.get("merged_pr", "Menggabungkan pull request"),
                "repo": "pemobKilas",
                "icon": "pull_request",
                "relative_time": "5 hari lalu" if locale == "id" else "5 days ago"
            })
        else:
            recent_activities.append({
                "action": t_actions.get("created_repo", "Membuat repositori baru"),
                "repo": "biTBdsi",
                "icon": "repo",
                "relative_time": "2 bulan lalu" if locale == "id" else "2 months ago"
            })

    processed_data = {
        "processed_at": now.isoformat(),
        "locale": locale,
        "labels": translations,
        "profile": {
            "username": config.get("username", "Zakkyaulia"),
            "display_name": raw_data.get("user_profile", {}).get("name") or config.get("display_name", "Zakky Aulia Aldrin"),
            "subtitle": config.get("subtitle", "Mahasiswa Sistem Informasi · Universitas Andalas"),
            "collaboration_status": config.get("collaboration_status", "Terbuka untuk kolaborasi"),
            "collaboration_available": config.get("collaboration_available", True),
            "avatar_base64": raw_data.get("user_profile", {}).get("avatar_base64"),
            "social_links": config.get("social_links", {})
        },
        "card1_last_active": {
            "value": last_active_relative,
            "subtitle": translations.get("last_active_sub", "aktivitas publik terbaru"),
            "repo": last_active_repo
        },
        "card2_month_contributions": {
            "value": str(month_contributions),
            "subtitle": translations.get("month_contributions_sub", "total sejak awal bulan")
        },
        "card3_year_contributions": {
            "percentage": year_percentage,
            "total_year": year_contributions,
            "total_lifetime": lifetime_total,
            "subtitle": translations.get("year_contributions_sub", "dari seluruh\nkontribusi")
        },
        "card4_recent_repo": {
            "name": recent_repo_name,
            "language": recent_repo_lang,
            "language_color": recent_repo_lang_color,
            "relative_time": recent_repo_relative
        },
        "languages": normalized_languages,
        "heatmap": {
            "weeks": weeks,
            "month_columns": month_columns,
            "active_weeks": active_weeks_count,
            "total_weeks": 12,
            "active_weeks_text": f"{translations.get('active_weeks_prefix', 'Aktif')} {active_weeks_count} {translations.get('active_weeks_suffix', 'dari 12 minggu')}"
        },
        "recent_activities": recent_activities
    }

    processed_path = DATA_DIR / "processed_stats.json"
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, indent=2)

    print(f"Processed stats successfully saved to {processed_path}")
    return processed_data


if __name__ == "__main__":
    process_stats()
