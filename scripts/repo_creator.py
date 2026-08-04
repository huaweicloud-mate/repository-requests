#!/usr/bin/env python3
"""Repository Creator for huaweicloud-mate - GOAT v1.1"""

import json, os, re, base64
import urllib.request, urllib.error

ORG = os.environ.get("ORG_NAME", "huaweicloud-mate")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
EVENT_PATH = os.environ.get("GITHUB_EVENT_PATH", "")

GITCODE_ORG = os.environ.get("GITCODE_ORG", "hd-vector")
GITCODE_USERNAME = os.environ.get("GITCODE_USERNAME", "")
GITCODE_TOKEN = os.environ.get("GITCODE_TOKEN", "")
GITCODE_API = os.environ.get("GITCODE_API", "https://gitcode.com/api/v5")

FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_ADMIN_OPEN_ID = os.environ.get("FEISHU_ADMIN_OPEN_ID", "")

GITHUB_API = "https://api.github.com"
BOT_HDR = {"Authorization": f"Bearer {BOT_TOKEN}", "Accept": "application/vnd.github+json"}
GH_HDR = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
GC_HDR = {"PRIVATE-TOKEN": GITCODE_TOKEN, "Content-Type": "application/json"}

PRODUCT_TYPES = ["SDK", "Terraform Provider", "GitHub Action", "framework", "Exporter / Plugin", "IoT SDK"]
SAMPLE_TYPES = ["sample"]
DOCS_TYPES = ["docs"]
INTERNAL_TYPES = ["internal"]


def api(method, path, auth="bot", data=None):
    headers = BOT_HDR if auth == "bot" else GH_HDR
    url = f"{GITHUB_API}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return None if resp.status == 204 else json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:300]
        print(f"GH API {method} {path}: {e.code} {err}")
        return None


def gc_api(method, path, data=None):
    if not GITCODE_TOKEN:
        return None
    url = f"{GITCODE_API}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=GC_HDR, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return None if resp.status == 204 else json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:300]
        print(f"GC API {method} {path}: {e.code} {err}")
        return None


def load_event():
    with open(EVENT_PATH) as f:
        return json.load(f)


def b64(s):
    return base64.b64encode(s.encode()).decode()


def put_file(repo, path, content, msg):
    api("PUT", f"/repos/{ORG}/{repo}/contents/{path}", "bot", {"message": msg, "content": b64(content)})


def add_labels(repo, labels):
    for name in labels:
        api("POST", f"/repos/{ORG}/{repo}/labels", "bot", {"name": name, "color": "ededed"})


def set_role(repo, role, users):
    role_map = {"owner": "admin", "maintainer": "maintain", "writer": "push"}
    for user in users:
        api("PUT", f"/repos/{ORG}/{repo}/collaborators/{user}", "bot", {"permission": role_map.get(role, "push")})


def validate_name(name):
    return bool(re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', name)) and len(name) <= 100


def validate_topics(raw):
    topics = re.split(r'[,\n]+', raw.strip())
    return [t.strip().lower() for t in topics if re.match(r'^[a-z0-9][a-z0-9.-]*$', t.strip())]


def get_license(repo_type, user_choice):
    if repo_type in PRODUCT_TYPES:
        return {"Apache-2.0": "Apache-2.0", "MIT": "MIT", "BSD-3-Clause": "BSD-3-Clause"}.get(user_choice, "Apache-2.0")
    return "Apache-2.0"


def get_readme(name, repo_type, license_name, desc):
    tmpl = """# {name}

{desc}

## Quick Start

```bash
# TBD
```

## License

{license}
"""
    return tmpl.format(name=name, desc=desc, license=license_name)


CONTRIBUTING = """# Contributing

See README for setup.

## Commit Convention

feat: / fix: / docs: / style: / refactor: / test: / chore:

## PR Process

1. Fork and create branch
2. Commit changes
3. Open Pull Request
4. At least 2 approvals + CI pass required
"""

SECURITY = """# Security Policy

Report vulnerabilities to security@huaweicloud-mate.dev.

Do NOT disclose in public issues.
"""

COC = """# Code of Conduct

See organization-level CODE_OF_CONDUCT.md
"""

BUG_YML = """name: Bug Report
description: Report a bug
labels: ["type/bug"]
body:
  - type: textarea
    attributes:
      label: Description
    validations:
      required: true
"""

FEATURE_YML = """name: Feature Request
description: Request a feature
labels: ["type/feature"]
body:
  - type: textarea
    attributes:
      label: Description
    validations:
      required: true
"""

CONFIG_YML = "blank_issues_enabled: false\n"

PR_TEMPLATE = """## Summary

## Related Issue
Fixes #

## Checklist
- [ ] CI passed
- [ ] Reviewed
"""

TRIAGE_WF = """name: Issue Triage
on:
  issues:
    types: [opened]
permissions:
  issues: write
  contents: read
jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - uses: huaweicloud-mate/.github/actions/issue-bot@main
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
"""

SYNC_WF = """name: Sync to GitCode
on:
  push:
    branches: [main]
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: |
          git remote add gitcode https://GITCODE_USER_PLACEHOLDER:${{ secrets.GITCODE_TOKEN }}@gitcode.com/GITCODE_ORG_PLACEHOLDER/${{ github.event.repository.name }}.git 2>/dev/null || true
          git push gitcode main --force
""".replace("GITCODE_USER_PLACEHOLDER", GITCODE_USERNAME).replace("GITCODE_ORG_PLACEHOLDER", GITCODE_ORG)

DEPENDABOT = """version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
"""

LABELS_14 = ["type/bug", "type/enhancement", "type/question", "type/documentation",
             "priority/critical", "priority/high", "priority/medium", "priority/low",
             "status/pending", "status/in-progress", "status/blocked",
             "good first issue", "help wanted", "agent/triaged"]

LABELS_8 = LABELS_14[:8]


def get_level(repo_type):
    if repo_type in PRODUCT_TYPES: return "product", 14
    if repo_type in SAMPLE_TYPES: return "sample", 7
    if repo_type in DOCS_TYPES: return "docs", 3
    return "internal", 2


def create_gitcode_repo(repo_name, desc):
    group = gc_api("GET", f"/groups/{GITCODE_ORG}")
    if not group or "id" not in group:
        print(f"Failed to get GitCode group {GITCODE_ORG}")
        return None
    result = gc_api("POST", "/projects", {
        "name": repo_name, "path": repo_name, "namespace_id": group["id"],
        "description": desc or "", "visibility": "public", "initialize_with_readme": False
    })
    if result and "id" in result:
        url = result.get("web_url", f"https://gitcode.com/{GITCODE_ORG}/{repo_name}")
        print(f"GitCode repo created: {url}")
        return url
    return None


def notify_feishu(repo_name, repo_type, url):
    if not all([FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_ADMIN_OPEN_ID]):
        return
    try:
        data = json.dumps({"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}).encode()
        req = urllib.request.Request("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                                     data=data, headers={"Content-Type": "application/json"})
        token = json.loads(urllib.request.urlopen(req, timeout=10).read()).get("tenant_access_token", "")
        if not token:
            return
        card = {"config": {"wide_screen_mode": True},
                "header": {"title": {"tag": "plain_text", "content": "Repo Created"}, "template": "turquoise"},
                "elements": [{"tag": "markdown", "content": f"**{repo_name}** ({repo_type})\n{url}"}]}
        urllib.request.urlopen(urllib.request.Request(
            f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
            data=json.dumps({"receive_id": FEISHU_ADMIN_OPEN_ID, "msg_type": "interactive",
                             "content": json.dumps(card, ensure_ascii=False)}).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}), timeout=10)
        print("Feishu notification sent")
    except Exception as e:
        print(f"Feishu: {e}")


def main():
    event = load_event()
    issue = event.get("issue", {})
    num = issue.get("number", 0)
    labels = [l["name"] for l in issue.get("labels", [])]
    body = issue.get("body", "")
    author = issue.get("user", {}).get("login", "")

    if "status/approved" not in labels:
        print("Not approved, skip")
        return

    print(f"Processing #{num}: {issue.get('title','')}")

    # Parse fields
    lines = body.split("\n")
    fields = {}
    for i, line in enumerate(lines):
        for prefix in ["### Repo Type", "### Repo Name", "### Description", "### Visibility",
                        "### License", "### Topics", "### Owner", "### Maintainer", "### Writer",
                        "### Reason"]:
            if line.startswith(prefix):
                key = prefix.replace("### ", "").lower().replace(" ", "_")
                for j in range(i + 1, min(i + 3, len(lines))):
                    v = lines[j].strip().lstrip("_No response_").strip()
                    if v and not v.startswith("###") and not v.startswith("_"):
                        fields[key] = v
                        break
                break

    repo_type = fields.get("repo_type", "SDK")
    repo_name = fields.get("repo_name", "").strip().lower()
    desc = fields.get("description", "")
    visibility = fields.get("visibility", "public").lower()
    license_choice = fields.get("license", "Apache-2.0")
    topics_raw = fields.get("topics", "")
    owners_str = fields.get("owner", "")
    maint_str = fields.get("maintainer", "")
    writer_str = fields.get("writer", "")
    justification = fields.get("reason", "")

    print(f"Type: {repo_type}, Name: {repo_name}")

    if not validate_name(repo_name):
        api("POST", f"/repos/{ORG}/repository-requests/issues/{num}/comments", "gh",
            {"body": f"Invalid repo name: `{repo_name}`"})
        return

    topics = validate_topics(topics_raw)
    if len(topics) < 3:
        api("POST", f"/repos/{ORG}/repository-requests/issues/{num}/comments", "gh",
            {"body": f"Need >=3 valid topics, got {len(topics)}"})
        return

    existing = api("GET", f"/repos/{ORG}/{repo_name}", "bot")
    if existing and "id" in existing:
        api("POST", f"/repos/{ORG}/repository-requests/issues/{num}/comments", "gh",
            {"body": f"Repo already exists: `{ORG}/{repo_name}`"})
        return

    license_name = get_license(repo_type, license_choice)
    level, init_count = get_level(repo_type)

    create_data = {
        "name": repo_name, "description": desc, "private": visibility == "private",
        "auto_init": True, "has_issues": True, "has_projects": False, "has_wiki": False,
        "allow_squash_merge": True, "allow_merge_commit": False, "allow_rebase_merge": False,
    }
    result = api("POST", f"/orgs/{ORG}/repos", "bot", create_data)
    if not result or "id" not in result:
        print(f"Failed to create repo: {result}")
        return

    repo_url = result["html_url"]
    print(f"GitHub repo created: {repo_url}")

    # Initialize files
    readme = get_readme(repo_name, repo_type, license_name, desc)
    put_file(repo_name, "README.md", readme, "Init README")
    put_file(repo_name, "LICENSE", f"{license_name} License", f"Add {license_name} license")

    if level in ("product", "sample"):
        put_file(repo_name, "CONTRIBUTING.md", CONTRIBUTING, "Add CONTRIBUTING")
    if level == "product":
        put_file(repo_name, "SECURITY.md", SECURITY, "Add SECURITY")
        put_file(repo_name, "CODE_OF_CONDUCT.md", COC, "Add CODE_OF_CONDUCT")
    if level in ("product", "sample"):
        put_file(repo_name, ".github/ISSUE_TEMPLATE/bug_report.yml", BUG_YML, "Add bug template")
        put_file(repo_name, ".github/ISSUE_TEMPLATE/feature_request.yml", FEATURE_YML, "Add feature template")
        put_file(repo_name, ".github/ISSUE_TEMPLATE/config.yml", CONFIG_YML, "Add issue config")
        put_file(repo_name, ".github/PULL_REQUEST_TEMPLATE.md", PR_TEMPLATE, "Add PR template")
    if level == "product":
        put_file(repo_name, ".github/dependabot.yml", DEPENDABOT, "Add dependabot")
        put_file(repo_name, ".github/workflows/triage-issue.yml", TRIAGE_WF, "Add triage workflow")
        put_file(repo_name, ".github/workflows/sync-to-gitcode.yml", SYNC_WF, "Add GitCode sync")

    # Labels
    if level == "product":
        add_labels(repo_name, LABELS_14)
    elif level == "sample":
        add_labels(repo_name, LABELS_8)

    # Topics
    api("PUT", f"/repos/{ORG}/{repo_name}/topics", "bot", {"names": topics[:20]})

    # Roles
    owners = [u.strip() for u in re.split(r'[,\n]+', owners_str) if u.strip()]
    maintainers = [u.strip() for u in re.split(r'[,\n]+', maint_str) if u.strip()]
    writers = [u.strip() for u in re.split(r'[,\n]+', writer_str) if u.strip()]

    for u in owners:
        set_role(repo_name, "owner", [u])
    for u in maintainers:
        if u not in owners:
            set_role(repo_name, "maintainer", [u])
    for u in writers:
        if u not in owners and u not in maintainers:
            set_role(repo_name, "writer", [u])

    # GitCode sync
    gc_url = create_gitcode_repo(repo_name, desc)

    # Close issue
    lines = [
        f"## Repo Created",
        f"",
        f"| Item | Detail |",
        f"|------|--------|",
        f"| GitHub | [{ORG}/{repo_name}]({repo_url}) |",
    ]
    if gc_url:
        lines.append(f"| GitCode | [{GITCODE_ORG}/{repo_name}]({gc_url}) |")
    lines += [f"| Type | {repo_type} ({level}) |", f"| License | {license_name} |",
              f"| Init | {init_count} items |", f"| Visibility | {visibility} |"]
    api("POST", f"/repos/{ORG}/repository-requests/issues/{num}/comments", "gh", {"body": "\n".join(lines)})
    api("POST", f"/repos/{ORG}/repository-requests/issues/{num}/labels", "gh", {"labels": ["status/completed"]})
    api("PATCH", f"/repos/{ORG}/repository-requests/issues/{num}", "gh", {"state": "closed"})

    notify_feishu(repo_name, repo_type, repo_url)
    print("Done.")


if __name__ == "__main__":
    main()
