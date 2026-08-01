#!/usr/bin/env python3
"""
Repository Creator Bot
Reads a repo-creation Issue, creates the repo, initializes it, and closes the Issue.
"""
import json
import os
import sys
import re
import urllib.request
import urllib.error

def github_api(method, path, data=None, token=None):
    """Call GitHub REST API"""
    url = f"https://api.github.com{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "repo-creator-bot"
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status in (200, 201, 204):
                if resp.status == 204:
                    return {"status": "success"}
                return json.loads(resp.read())
            return None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:500]
        print(f"GitHub API error {e.code}: {error_body}", file=sys.stderr)
        return {"error": error_body, "status_code": e.code}
    except Exception as e:
        print(f"API error: {e}", file=sys.stderr)
        return {"error": str(e)}

def parse_issue_body(body):
    """Parse the YAML-like issue body from GitHub Issue form"""
    fields = {}
    # GitHub form issues use ### as section headers
    # Pattern: ### Field Name\n\nvalue
    sections = re.split(r'### ', body)
    for section in sections[1:]:  # skip first empty part
        lines = section.strip().split('\n')
        if not lines:
            continue
        field_name = lines[0].strip()
        value = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''
        # Remove "No response" placeholder
        if value == '_No response_':
            value = ''
        fields[field_name] = value
    return fields

def validate_repo_name(name):
    """Validate repo name follows GitHub naming rules"""
    if not name:
        return False, "仓库名称不能为空"
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', name) and not re.match(r'^[a-z0-9]$', name):
        return False, "仓库名称只能包含小写字母、数字和连字符，且不能以连字符开头或结尾"
    if len(name) > 100:
        return False, "仓库名称不能超过100个字符"
    if '--' in name:
        return False, "仓库名称不能包含连续连字符"
    return True, ""

def check_repo_exists(org, name, token):
    """Check if a repo with this name already exists"""
    result = github_api("GET", f"/repos/{org}/{name}", token=token)
    if isinstance(result, dict) and "error" not in result and "id" in result:
        return True
    return False

def create_repo(org, name, description, visibility, token):
    """Create a new repository in the organization"""
    data = {
        "name": name,
        "description": description,
        "private": visibility == "private",
        "has_issues": True,
        "has_projects": True,
        "has_wiki": False,
        "auto_init": True,  # Create with README
    }
    return github_api("POST", f"/orgs/{org}/repos", data, token=token)

def set_repo_topics(org, name, topics, token):
    """Set repository topics"""
    data = {"names": topics}
    return github_api("PUT", f"/repos/{org}/{name}/topics", data, token=token)

def add_label(org, repo, name, color, description, token):
    """Add a label to the repo"""
    data = {"name": name, "color": color, "description": description}
    return github_api("POST", f"/repos/{org}/{repo}/labels", data, token=token)

def create_file_in_repo(org, repo, path, content, message, token, branch="main"):
    """Create a file in the repo"""
    import base64
    encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')
    data = {"message": message, "content": encoded, "branch": branch}
    return github_api("PUT", f"/repos/{org}/{repo}/contents/{path}", data, token=token)

def initialize_repo(org, repo_name, language, license_name, description, token):
    """Initialize the new repo with standard community files"""
    results = []
    
    # 1. Create labels
    labels_to_create = [
        ("bug", "d73a4a", "Bug report"),
        ("enhancement", "a2eeef", "Feature request"),
        ("question", "d876e3", "Question"),
        ("documentation", "0075ca", "Documentation"),
        ("good first issue", "7057ff", "Good for newcomers"),
        ("help wanted", "008672", "Extra attention needed"),
        ("priority/critical", "b60205", "Critical priority"),
        ("priority/high", "d93f0b", "High priority"),
        ("priority/medium", "fbca04", "Medium priority"),
        ("priority/low", "0e8a16", "Low priority"),
        ("agent/triaged", "bfd4f2", "Automatically triaged by AI agent"),
        ("status/pending", "fbca04", "Pending review"),
        ("status/in-progress", "1d76db", "Work in progress"),
        ("status/blocked", "b60205", "Blocked"),
    ]
    for name, color, desc in labels_to_create:
        r = add_label(org, repo_name, name, color, desc, token)
        if r and "error" not in r:
            results.append(f"  label: {name}")
    
    # 2. Create CONTRIBUTING.md
    contributing = f"""# 贡献指南

感谢您对 `{repo_name}` 项目的关注！

## 如何贡献

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 开发流程

- 所有 PR 需要至少 1 个 review
- CI 必须通过才能合入
- 遵循项目的代码风格

## 问题反馈

- Bug 报告：使用 Issue 模板
- 功能建议：使用 Issue 模板
- 安全漏洞：请通过邮件私密报告
"""
    r = create_file_in_repo(org, repo_name, "CONTRIBUTING.md", contributing,
                           "chore: add CONTRIBUTING.md", token)
    if r and "error" not in r:
        results.append("  CONTRIBUTING.md")

    # 3. Create SECURITY.md
    security = f"""# 安全策略

## 报告安全漏洞

**请勿通过GitHub Issue公开报告安全漏洞。**

请发送邮件至 huaweicloud-mate@huawei.com 报告安全漏洞。

我们承诺：
- 48小时内确认收到报告
- 7天内提供初步评估
- 修复后及时通知报告者
"""
    r = create_file_in_repo(org, repo_name, "SECURITY.md", security,
                           "chore: add SECURITY.md", token)
    if r and "error" not in r:
        results.append("  SECURITY.md")

    # 4. Create .github/dependabot.yml
    dependabot = """version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
"""
    r = create_file_in_repo(org, repo_name, ".github/dependabot.yml", dependabot,
                           "chore: add dependabot config", token)
    if r and "error" not in r:
        results.append("  dependabot.yml")

    # 5. Create .github/stale.yml
    stale = """daysUntilStale: 60
daysUntilClose: 7
staleLabel: stale
markComment: >
  This issue has been automatically marked as stale because it has not had
  recent activity. It will be closed if no further activity occurs.
closeComment: >
  This issue has been automatically closed due to inactivity.
"""
    r = create_file_in_repo(org, repo_name, ".github/stale.yml", stale,
                           "chore: add stale bot config", token)
    if r and "error" not in r:
        results.append("  stale.yml")

    # 6. Enable vulnerability alerts and security fixes
    github_api("PUT", f"/repos/{org}/{repo_name}/vulnerability-alerts", token=token)
    github_api("PUT", f"/repos/{org}/{repo_name}/automated-security-fixes", token=token)
    results.append("  security alerts + auto fixes")

    # 7. Create Issue templates
    bug_template = """name: 🐛 Bug Report
description: Report a bug
labels: ["bug"]
body:
  - type: textarea
    id: description
    attributes:
      label: Description
      description: Describe the bug
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Steps to Reproduce
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
    validations:
      required: true
  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
    validations:
      required: true
  - type: textarea
    id: environment
    attributes:
      label: Environment
"""
    r = create_file_in_repo(org, repo_name, ".github/ISSUE_TEMPLATE/bug_report.yml",
                           bug_template, "chore: add bug report template", token)
    if r and "error" not in r:
        results.append("  bug_report.yml")

    feature_template = """name: ✨ Feature Request
description: Request a new feature
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: Problem Statement
      description: What problem does this feature solve?
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives Considered
"""
    r = create_file_in_repo(org, repo_name, ".github/ISSUE_TEMPLATE/feature_request.yml",
                           feature_template, "chore: add feature request template", token)
    if r and "error" not in r:
        results.append("  feature_request.yml")

    template_config = """blank_issues_enabled: false
"""
    r = create_file_in_repo(org, repo_name, ".github/ISSUE_TEMPLATE/config.yml",
                           template_config, "chore: add issue template config", token)
    if r and "error" not in r:
        results.append("  issue config.yml")

    # 8. Add Triage Agent workflow (if LLM_API_KEY is available)
    triage_workflow = """name: Triage Issue

on:
  issues:
    types: [opened, edited]

permissions:
  issues: write
  contents: read

jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout .github org repo
        uses: actions/checkout@v4
        with:
          repository: ${{ github.repository_owner }}/.github
          path: .github-repo
          ref: main
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Run Triage Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ''
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          LLM_MODEL: 'glm-4-flash'
          LLM_ENDPOINT: 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
          CONFIDENCE_THRESHOLD: '0.7'
          DRY_RUN: 'false'
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_EVENT_PATH: ${{ github.event_path }}
        run: python3 .github-repo/actions/triage/triage_agent.py
"""
    r = create_file_in_repo(org, repo_name, ".github/workflows/triage-issue.yml",
                           triage_workflow, "feat: enable Triage Agent", token)
    if r and "error" not in r:
        results.append("  triage-issue.yml")

    return results

def main():
    # Read environment
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    org = os.environ.get("ORG_NAME", "huaweicloud-mate")
    bot_token = os.environ.get("BOT_TOKEN", token)  # PAT with org repo creation rights
    
    if not event_path or not os.path.exists(event_path):
        print("No event payload found")
        return

    with open(event_path) as f:
        event = json.load(f)

    issue = event.get("issue", {})
    issue_number = issue.get("number", 0)
    issue_title = issue.get("title", "")
    issue_body = issue.get("body", "") or ""
    issue_labels = [l["name"] for l in issue.get("labels", [])]
    repo_full = os.environ.get("GITHUB_REPOSITORY", "")
    
    print(f"Processing Issue #{issue_number}: {issue_title}")
    print(f"Labels: {issue_labels}")

    # Only process issues with the correct label
    if "request/create-repo" not in issue_labels:
        print("Not a repo creation request, skipping")
        return

    # Check if already processed
    if "status/completed" in issue_labels or "status/failed" in issue_labels:
        print("Already processed, skipping")
        return

    # Parse issue body
    fields = parse_issue_body(issue_body)
    print(f"Parsed fields: {json.dumps(fields, ensure_ascii=False)}")

    # Extract field values (matching the template field names)
    repo_name = fields.get("仓库名称", "").strip()
    description = fields.get("仓库描述", "").strip()
    visibility = fields.get("可见性", "public").strip().lower()
    language = fields.get("主要编程语言", "Python").strip()
    license_name = fields.get("开源许可证", "Apache-2.0").strip()
    topics_str = fields.get("仓库标签（Topics）", "").strip()
    justification = fields.get("申请理由", "").strip()

    # Validate repo name
    valid, msg = validate_repo_name(repo_name)
    if not valid:
        error_msg = f"❌ 仓库名称验证失败: {msg}\n\n请修改后重新提交。"
        github_api("POST", f"/repos/{repo_full}/issues/{issue_number}/comments",
                   {"body": error_msg}, token=token)
        github_api("POST", f"/repos/{repo_full}/issues/{issue_number}/labels",
                   {"labels": ["status/failed"]}, token=token)
        print(f"Validation failed: {msg}")
        return

    # Check if repo already exists
    if check_repo_exists(org, repo_name, bot_token):
        error_msg = f"❌ 仓库 `{org}/{repo_name}` 已存在！\n\n请选择其他名称后重新提交。"
        github_api("POST", f"/repos/{repo_full}/issues/{issue_number}/comments",
                   {"body": error_msg}, token=token)
        github_api("POST", f"/repos/{repo_full}/issues/{issue_number}/labels",
                   {"labels": ["status/failed"]}, token=token)
        print(f"Repo already exists: {org}/{repo_name}")
        return

    # Post progress comment
    progress_msg = f"### 🤖 仓库创建机器人\n\n⏳ 正在处理建仓请求...\n\n- 仓库名称: `{repo_name}`\n- 可见性: {visibility}\n- 语言: {language}\n- 许可证: {license_name}\n\n请稍候，预计需要 30-60 秒。"
    github_api("POST", f"/repos/{repo_full}/issues/{issue_number}/comments",
               {"body": progress_msg}, token=token)

    # Update label to in-progress
    github_api("POST", f"/repos/{repo_full}/issues/{issue_number}/labels",
               {"labels": ["status/in-progress"]}, token=token)

    # Create the repository
    print(f"Creating repo: {org}/{repo_name}")
    result = create_repo(org, repo_name, description, visibility, bot_token)
    
    if not result or (isinstance(result, dict) and "error" in result):
        error_detail = result.get("error", "Unknown error") if isinstance(result, dict) else "Unknown error"
        error_msg = f"### 🤖 仓库创建机器人\n\n❌ 创建仓库失败！\n\n```\n{error_detail}\n```\n\n请检查错误信息，修改后重新提交。"
        github_api("POST", f"/repos/{repo_full}/issues/{issue_number}/comments",
                   {"body": error_msg}, token=token)
        github_api("POST", f"/repos/{repo_full}/issues/{issue_number}/labels",
                   {"labels": ["status/failed"]}, token=token)
        print(f"Failed to create repo: {error_detail}")
        return

    repo_url = result.get("html_url", "")
    print(f"Repo created: {repo_url}")

    # Set topics
    topics = [t.strip() for t in topics_str.split(",") if t.strip()] if topics_str else []
    if topics:
        set_repo_topics(org, repo_name, topics, bot_token)
        print(f"Topics set: {topics}")

    # Initialize the repo with community files
    print("Initializing repo with community files...")
    init_results = initialize_repo(org, repo_name, language, license_name, description, bot_token)
    print(f"Initialized: {len(init_results)} items")

    # Build success comment
    success_parts = [
        f"### 🤖 仓库创建机器人\n",
        f"✅ 仓库创建成功！\n",
        f"| 属性 | 值 |\n",
        f"|------|----|\n",
        f"| 仓库 | [`{org}/{repo_name}`]({repo_url}) |\n",
        f"| 可见性 | {visibility} |\n",
        f"| 语言 | {language} |\n",
        f"| 许可证 | {license_name} |\n",
    ]
    if topics:
        success_parts.append(f"| Topics | {', '.join(topics)} |\n")
    success_parts.append(f"\n**初始化内容：**\n")
    for item in init_results:
        success_parts.append(f"- {item}\n")
    success_parts.append(f"\n仓库已包含基础社区治理配置，可以开始开发了！🚀\n")
    success_parts.append(f"\n<sub>repo-creator-bot v1.0</sub>")

    success_msg = "".join(success_parts)
    github_api("POST", f"/repos/{repo_full}/issues/{issue_number}/comments",
               {"body": success_msg}, token=token)

    # Update labels
    github_api("POST", f"/repos/{repo_full}/issues/{issue_number}/labels",
               {"labels": ["status/completed"]}, token=token)

    # Close the issue
    github_api("PATCH", f"/repos/{repo_full}/issues/{issue_number}",
               {"state": "closed", "state_reason": "completed"}, token=token)

    print(f"Issue #{issue_number} closed successfully")

if __name__ == "__main__":
    main()
