#!/usr/bin/env python3
"""
huaweicloud-mate � ��仓机器人 — 按 GOAT 建仓流程文� � v1.1
支持 9 种仓库类型 → 4 个等� ��初始化（2~14 项）
"""

import json, o s, re, time
import urllib.request, urllib.err or

ORG = os.environ.get("ORG_NAME", "huaweic loud-mate")
BOT_TOKEN = os.environ.get("BOT_T OKEN", "")
GITHUB_TOKEN = os.environ.get("GIT HUB_TOKEN", "")
EVENT_PATH = os.environ.get(" GITHUB_EVENT_PATH", "")

GITCODE_ORG = os.env iron.get("GITCODE_ORG", "hd-vector")
GITCODE_ USERNAME = os.environ.get("GITCODE_USERNAME",  "")
GITCODE_TOKEN = os.environ.get("GITCODE_ TOKEN", "")

FEISHU_APP_ID = os.environ.get(" FEISHU_APP_ID", "")
GITCODE_API = "https://gi tcode.com/api/v4"
GC_HEADERS = {"PRIVATE-TOKE N": GITCODE_TOKEN, "Content-Type": "applicati on/json"}

FEISHU_APP_ID = os.environ.get("FE ISHU_APP_ID", "")
FEISHU_APP_SECRET = os.envi ron.get("FEISHU_APP_SECRET", "")
FEISHU_ADMIN _OPEN_ID = os.environ.get("FEISHU_ADMIN_OPEN_ ID", "")

GITHUB_API = "https://api.github.co m"
BOT_HEADERS = {"Authorization": f"Bearer { BOT_TOKEN}", "Accept": "application/vnd.githu b+json"}
GH_HEADERS = {"Authorization": f"Bea rer {GITHUB_TOKEN}", "Accept": "application/v nd.github+json"}

# ─── 类型→等级 映射 ───
PRODUCT_TYPES = ["SDK", "Ter raform Provider", "GitHub Action", "框架集 成", "Exporter / Plugin", "IoT SDK"]
SAMPLE_ TYPES = ["示例 / Lab / Sample"]
DOCS_TYPES  = ["文档 / 数据集"]
INTERNAL_TYPES = ["� ��部配置"]


def api(method, path, token=N one, data=None):
    headers = BOT_HEADERS if  token == "bot" else GH_HEADERS
    url = f"{ GITHUB_API}{path}"
    body = json.dumps(data ).encode() if data else None
    req = urllib .request.Request(url, data=body, headers=head ers, method=method)
    try:
        with url lib.request.urlopen(req, timeout=30) as resp: 
            if resp.status == 204:
                 return None
            return json.lo ads(resp.read())
    except urllib.error.HTTP Error as e:
        err = e.read().decode()[: 500]
        print(f"API {method} {path}: {e. code} {err}")
        return None


def load_ event():
    with open(EVENT_PATH) as f:
         return json.load(f)


def gitcode_api(met hod, path, data=None):
    """调用 GitCode  API（GitLab 兼容）"""
    if not GITCODE_ TOKEN:
        print("GITCODE_TOKEN not set,  skipping GitCode API")
        return None
     url = f"{GITCODE_API}{path}"
    body = jso n.dumps(data).encode() if data else None
     req = urllib.request.Request(url, data=body,  headers=GC_HEADERS, method=method)
    try:
         with urllib.request.urlopen(req, timeo ut=30) as resp:
            if resp.status ==  204:
                return None
             return json.loads(resp.read())
    except ur llib.error.HTTPError as e:
        err = e.re ad().decode()[:500]
        print(f"GitCode A PI {method} {path}: {e.code} {err}")
         return None


def create_gitcode_repo(repo_na me, description):
    """在 GitCode 上创� �同名仓库"""
    # 获取 hd-vector group  的 ID
    group_url = f"/groups/{GITCODE_OR G}"
    group = gitcode_api("GET", group_url) 
    if not group or "id" not in group:
         print(f"Failed to get GitCode group {GITCO DE_ORG}")
        return None

    namespace_ id = group["id"]
    data = {
        "name":  repo_name,
        "path": repo_name,
         "namespace_id": namespace_id,
        "desc ription": description or "",
        "visibil ity": "public",
        "initialize_with_read me": False,
    }
    result = gitcode_api("P OST", "/projects", data)
    if result and "i d" in result:
        gitcode_url = result.ge t("web_url", f"https://gitcode.com/{GITCODE_O RG}/{repo_name}")
        print(f"GitCode rep o created: {gitcode_url}")
        return git code_url
    print(f"Failed to create GitCode  repo")
    return None


# ─── 许可� ��策略 ───
def get_license(repo_type,  user_choice):
    if repo_type in PRODUCT_TY PES:
        choice_map = {"Apache-2.0（推� ��）": "Apache-2.0", "Apache-2.0": "Apache-2 .0", "MIT": "MIT", "BSD-3-Clause": "BSD-3-Cla use"}
        return choice_map.get(user_choi ce, "Apache-2.0")
    return "Apache-2.0"


#  ─── README 模板（9套） ───
 README_TEMPLATES = {
    "SDK": """# {name}
[ ![License](https://img.shields.io/badge/Licen se-{license}-blue.svg)](LICENSE)

{descriptio n}

## 安装
```bash
pip install {name}
```
 
## API 参考
待补充

## 贡献
查看 [C ONTRIBUTING.md](CONTRIBUTING.md)

## 许可� �
本项目使用 {license} 许可证。
""", 
    "Terraform Provider": """# {name}
[![Lic ense](https://img.shields.io/badge/License-{l icense}-blue.svg)](LICENSE)

{description}

# # Provider 配置
```hcl
provider "{name}" {{ 
  # 配置项
}}
```

## Resource / DataSour ce 列表
待补充

## 贡献
查看 [CONTRI BUTING.md](CONTRIBUTING.md)
""",
    "GitHub  Action": """# {name}
[![License](https://img. shields.io/badge/License-{license}-blue.svg)] (LICENSE)

{description}

## Inputs
| 参数  | 类型 | 必需 | 默认值 | 说明 |
|--- ---|------|------|--------|------|

## Output s
| 输出 | 说明 |
|------|------|

## 使 用示例
```yaml
- uses: huaweicloud-mate/{n ame}@v1
  with:
    param: value
```

## 贡� ��
查看 [CONTRIBUTING.md](CONTRIBUTING.md)
 """,
    "框架集成": """# {name}
[![Licen se](https://img.shields.io/badge/License-{lic ense}-blue.svg)](LICENSE)

{description}

##  快速集成
```bash
pip install {name}
```

 ## 配置说明
待补充

## 版本兼容
|  版本 | 兼容语言 / 框架 | 状态 |
|-- ----|----------------|------|

## 贡献
查� �� [CONTRIBUTING.md](CONTRIBUTING.md)
""",
     "Exporter / Plugin": """# {name}
[![License ](https://img.shields.io/badge/License-{licen se}-blue.svg)](LICENSE)

{description}

## � �署方式
```bash
docker run -d --name {name } huaweicloud-mate/{name}:latest
```

## 指� ��说明
待补充

## 贡献
查看 [CONTRIB UTING.md](CONTRIBUTING.md)
""",
    "IoT SDK" : """# {name}
[![License](https://img.shields .io/badge/License-{license}-blue.svg)](LICENS E)

{description}

## 硬件要求
待补充
 
## 设备接入示例
```python
from {name}  import Device
device = Device("device-id")
de vice.connect()
```

## 贡献
查看 [CONTRIB UTING.md](CONTRIBUTING.md)
""",
    "示例 /  Lab / Sample": """# {name}

{description}

# # 前置条件
- 语言环境
- 依赖安装
 
## 运行步骤
```bash
# 运行示例
```

 ## 效果展示
待补充
""",
    "文档 /  数据集": """# {name}

{description}

## � �容说明
待补充

## 使用方式
待补� ��
""",
    "内部配置": """# {name}

{des cription}

> 内部配置仓库

## 用途
� �补充

## 使用方式
待补充
""",
}


d ef make_readme(name, repo_type, license_name,  description):
    tmpl = README_TEMPLATES.ge t(repo_type, README_TEMPLATES["SDK"])
    ret urn tmpl.format(name=name, license=license_na me, description=description)


# ─── � �件模板 ───
CONTRIBUTING_MD = """# C ontributing to {name}

## 开发环境搭建
 见 README。

## 提交规范
使用约定� �提交：`feat:`, `fix:`, `docs:`, `style:`,  `refactor:`, `test:`, `chore:`

## PR 流程 
1. Fork 仓库
2. 创建分支 `feat/xxx`
3.  提交代码
4. 发起 Pull Request
5. 至� � 2 人 Review + CI 通过后合并

## Issue  规范
使用 Bug Report / Feature Request � ��板
"""

SECURITY_MD = """# Security Policy 

## 报告安全漏洞
如发现安全漏洞 ，请发送邮件至 security@huaweicloud-ma te.dev，**不要在公开 Issue 中披露**� ��

## 支持版本
| 版本 | 支持状态 | 
|------|---------|
| 最新 | ✅ 活跃支� �� |
"""

COC_MD = """# Contributor Covenant  Code of Conduct

## 我们的承诺
为了营 造一个开放和友好的环境，我们承 诺尊重所有参与者。

## 我们的标� ��
- 使用友好和包容的语言
- 尊重� ��同的观点和经验
- 建设性地接受� ��评

## 执行
违规行为可报告至项� ��维护者。
"""

BUG_REPORT_YML = """name:  Bug Report
description: 报告一个 bug
lab els: ["type/bug"]
body:
  - type: textarea
     attributes:
      label: 描述
      descr iption: 发生了什么
    validations:
       required: true
  - type: textarea
    attri butes:
      label: 复现步骤
  - type: te xtarea
    attributes:
      label: 期望行 为
  - type: textarea
    attributes:
       label: 环境信息
"""

FEATURE_YML = """nam e: Feature Request
description: 请求一个� ��功能
labels: ["type/feature"]
body:
  - t ype: textarea
    attributes:
      label: � �述
      description: 你希望添加什么 功能
    validations:
      required: true
   - type: textarea
    attributes:
      labe l: 使用场景
"""

CONFIG_YML = """blank_is sues_enabled: false
"""

PR_TEMPLATE = """##  变更说明


## 关联 Issue
Fixes #

## � �试
- [ ] 单元测试通过
- [ ] 手动测 试通过
"""

TRIAGE_WORKFLOW = """name: Iss ue Triage
on:
  issues:
    types: [opened]
p ermissions:
  issues: write
  contents: read
 jobs:
  triage:
    runs-on: ubuntu-latest
     steps:
      - uses: huaweicloud-mate/.gith ub/actions/issue-bot@main
        env:
           GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} 
"""

SYNC_WORKFLOW = f"""name: Sync to GitCo de
on:
  push:
    branches: [main]
permissio ns:
  contents: read
jobs:
  sync:
    runs-o n: ubuntu-latest
    steps:
      - uses: act ions/checkout@v4
        with:
          fetc h-depth: 0
      - run: |
          git remot e add gitcode https://{GITCODE_USERNAME}:${{{ { secrets.GITCODE_TOKEN }}}}@gitcode.com/{GIT CODE_ORG}/${{{{ github.event.repository.name  }}}}.git || true
          git push gitcode m ain --force
"""

DEPENDABOT = """version: 2
u pdates:
  - package-ecosystem: "github-action s"
    directory: "/"
    schedule:
      int erval: "weekly"
"""

LABELS_PRODUCT = ["type/ bug", "type/enhancement", "type/question", "t ype/documentation",
                  "priori ty/critical", "priority/high", "priority/medi um", "priority/low",
                  "statu s/pending", "status/in-progress", "status/blo cked",
                  "good first issue",  "help wanted", "agent/triaged"]
LABELS_SAMPLE  = LABELS_PRODUCT[:8]


def create_file(repo,  path, content, message):
    api("PUT", f"/r epos/{ORG}/{repo}/contents/{path}", "bot", {" message": message, "content": b64(content)})
 

def b64(s):
    import base64
    return ba se64.b64encode(s.encode()).decode()


def cre ate_labels(repo, labels):
    for name in lab els:
        api("POST", f"/repos/{ORG}/{repo }/labels", "bot", {"name": name, "color": "ed eded"})


def validate_repo_name(name):
    r eturn bool(re.match(r'^[a-z0-9]([a-z0-9-]*[a- z0-9])?$', name)) and len(name) <= 100


def  validate_topics(topics_str):
    topics = re. split(r'[,\n]+', topics_str.strip())
    vali d = []
    for t in topics:
        t = t.str ip().lower()
        if re.match(r'^[a-z0-9][ a-z0-9.-]*$', t):
            valid.append(t) 
    return valid


def assign_role(repo, rol e, users):
    if not users:
        return
     role_map = {"owner": "admin", "maintainer" : "maintain", "writer": "push"}
    perm = ro le_map.get(role, "push")
    for user in user s:
        api("PUT", f"/repos/{ORG}/{repo}/c ollaborators/{user}", "bot", {"permission": p erm})


def notify_feishu(repo_name, repo_typ e, url, author):
    if not all([FEISHU_APP_I D, FEISHU_APP_SECRET, FEISHU_ADMIN_OPEN_ID]): 
        return
    try:
        token_resp =  json.loads(urllib.request.urlopen(
             urllib.request.Request("https://open.feish u.cn/open-apis/auth/v3/tenant_access_token/in ternal",
                                   d ata=json.dumps({"app_id": FEISHU_APP_ID, "app _secret": FEISHU_APP_SECRET}).encode(),
                                    headers={"Conte nt-Type": "application/json"}), timeout=10).r ead())
        token = token_resp.get("tenant _access_token", "")
        if not token:
             return

        card = {
             "config": {"wide_screen_mode": True},
             "header": {"title": {"tag": "plain_text ", "content": "  仓库创建成功"}, "templ ate": "turquoise"},
            "elements": [ 
                {"tag": "markdown", "content ": f"**{author}** 申请的仓库已创建"}, 
                {"tag": "div", "fields": [
                     {"is_short": True, "text":  {"tag": "lark_md", "content": f"**仓库名� ��**\n{repo_name}"}},
                    {"i s_short": True, "text": {"tag": "lark_md", "c ontent": f"**类型**\n{repo_type}"}},
                 ]},
                {"tag": "action ", "actions": [
                    {"tag": " button", "text": {"tag": "plain_text", "conte nt": "查看仓库"}, "type": "primary", "url ": url},
                ]},
                 {"tag": "note", "elements": [{"tag": "plain_t ext", "content": "huaweicloud-mate Repo Creat or"}]}
            ]
        }
        urllib .request.urlopen(urllib.request.Request(
             f"https://open.feishu.cn/open-apis/im /v1/messages?receive_id_type=open_id",
             data=json.dumps({"receive_id": FEISHU_A DMIN_OPEN_ID, "msg_type": "interactive",
                              "content": json.dump s(card, ensure_ascii=False)}).encode(),
             headers={"Authorization": f"Bearer {to ken}", "Content-Type": "application/json"}),  timeout=10)
        print("Feishu notificatio n sent")
    except Exception as e:
        p rint(f"Feishu notification failed: {e}")


de f get_init_level(repo_type):
    if repo_type  in PRODUCT_TYPES:
        return "product"
     elif repo_type in SAMPLE_TYPES:
        re turn "sample"
    elif repo_type in DOCS_TYPE S:
        return "docs"
    else:
        re turn "internal"


def main():
    event = loa d_event()
    issue = event.get("issue", {})
     issue_number = issue.get("number", 0)
     labels = [l["name"] for l in issue.get("labe ls", [])]
    title = issue.get("title", "")
 
    if "status/approved" not in labels:
         print("Not approved, skipping")
        r eturn

    body = issue.get("body", "")
    a uthor = issue.get("user", {}).get("login", "" )

    # parse form fields (section header ->  next line is value)
    lines = body.split(" \n")
    fields = {}
    for i, line in enume rate(lines):
        for prefix in ["### 仓� ��类型", "### 仓库名称", "### 仓库描 述", "### 可见性",
                         "### 开源许可证", "### Topics 标签",  "### Owner", "### Maintainer",
                         "### Writer", "### 申请理由"]: 
            if line.startswith(prefix):
                 key = prefix.replace("### ", ""). strip()
                # value is on the nex t non-empty line
                for j in ran ge(i + 1, min(i + 3, len(lines))):
                     val = lines[j].strip()
                     if val and not val.startswith("###")  and not val.startswith("_"):
                         fields[key] = val
                         break
                break

    repo_ty pe = fields.get("仓库类型", "SDK")
    re po_name = fields.get("仓库名称", "").stri p().lower()
    description = fields.get("仓 库描述", "")
    visibility = fields.get(" 可见性", "public").lower()
    license_cho ice = fields.get("开源许可证", "Apache-2 .0")
    topics_raw = fields.get("Topics 标� ��", "")
    owner_str = fields.get("Owner",  "")
    maintainer_str = fields.get("Maintain er", "")
    writer_str = fields.get("Writer" , "")
    justification = fields.get("申请� ��由", "")

    print(f"Processing Issue #{i ssue_number}: {title}")
    print(f"Type: {re po_type}, Name: {repo_name}")

    if not val idate_repo_name(repo_name):
        api("POST ", f"/repos/{ORG}/repository-requests/issues/ {issue_number}/comments", "gh",
            { "body": f"  **仓库名称格式错误**：`{ repo_name}` 不符合规范（小写字母+� �字+连字符，≤100字符）"})
        r eturn

    topics = validate_topics(topics_ra w)
    if len(topics) < 3:
        api("POST" , f"/repos/{ORG}/repository-requests/issues/{ issue_number}/comments", "gh",
            {" body": f"  **Topics 不足**：至少需要 3  个合法标签（当前 {len(topics)} 个� �"})
        return

    # check duplicate
     existing = api("GET", f"/repos/{ORG}/{repo_ name}", "bot")
    if existing and "id" in ex isting:
        api("POST", f"/repos/{ORG}/re pository-requests/issues/{issue_number}/comme nts", "gh",
            {"body": f"  **仓库 已存在**：`{ORG}/{repo_name}` 已存在"} )
        return

    license_name = get_lice nse(repo_type, license_choice)
    level = ge t_init_level(repo_type)

    # create repo
     create_data = {
        "name": repo_name,
         "description": description,
        " private": visibility == "private",
        "a uto_init": True,
        "has_issues": True,
         "has_projects": False,
        "has_w iki": False,
        "allow_squash_merge": Tr ue,
        "allow_merge_commit": False,
         "allow_rebase_merge": False,
    }
    re sult = api("POST", f"/orgs/{ORG}/repos", "bot ", create_data)
    if not result or "id" not  in result:
        print(f"Failed to create  repo: {result}")
        return

    repo_url  = result["html_url"]
    print(f"Repo create d: {repo_url}")

    # init files
    readme  = make_readme(repo_name, repo_type, license_n ame, description)
    create_file(repo_name,  "README.md", readme, "Init README")
    creat e_file(repo_name, "LICENSE", f"{license_name}  License\n", f"Add {license_name} license")

     if level in ("product", "sample"):
         create_file(repo_name, "CONTRIBUTING.md", C ONTRIBUTING_MD.format(name=repo_name), "Add c ontributing guide")
    if level == "product" :
        create_file(repo_name, "SECURITY.md ", SECURITY_MD, "Add security policy")
         create_file(repo_name, "CODE_OF_CONDUCT.md" , COC_MD, "Add code of conduct")
    if level  in ("product", "sample"):
        create_fil e(repo_name, ".github/ISSUE_TEMPLATE/bug_repo rt.yml", BUG_REPORT_YML, "Add bug template")
         create_file(repo_name, ".github/ISSUE _TEMPLATE/feature_request.yml", FEATURE_YML,  "Add feature template")
        create_file(r epo_name, ".github/ISSUE_TEMPLATE/config.yml" , CONFIG_YML, "Add issue config")
        cre ate_file(repo_name, ".github/PULL_REQUEST_TEM PLATE.md", PR_TEMPLATE, "Add PR template")
     if level == "product":
        create_file( repo_name, ".github/dependabot.yml", DEPENDAB OT, "Add dependabot config")
        create_f ile(repo_name, ".github/workflows/triage-issu e.yml", TRIAGE_WORKFLOW, "Add triage workflow ")
        create_file(repo_name, ".github/wo rkflows/sync-to-gitcode.yml", SYNC_WORKFLOW,  "Add GitCode sync workflow")

    # labels
     if level == "product":
        create_label s(repo_name, LABELS_PRODUCT)
    elif level = = "sample":
        create_labels(repo_name,  LABELS_SAMPLE)

    # topics
    api("PUT", f "/repos/{ORG}/{repo_name}/topics", "bot",
         {"names": topics[:20]})

    # roles
     owners = [u.strip() for u in re.split(r'[,\n ]+', owner_str) if u.strip()]
    maintainers  = [u.strip() for u in re.split(r'[,\n]+', ma intainer_str) if u.strip()]
    writers = [u. strip() for u in re.split(r'[,\n]+', writer_s tr) if u.strip()]

    for u in owners:
         assign_role(repo_name, "owner", [u])
    f or u in maintainers:
        if u not in owne rs:
            assign_role(repo_name, "maint ainer", [u])
    for u in writers:
        if  u not in owners and u not in maintainers:
             assign_role(repo_name, "writer", [u ])

    # create GitCode mirror
    gitcode_u rl = create_gitcode_repo(repo_name, descripti on)

    # close issue
    init_count = {"pro duct": 14, "sample": 7, "docs": 3, "internal" : 2}[level]
    lines = [
        f"##  建� �完成",
        f"",
        f"| 项目 | � ��情 |",
        f"|------|------|",
         f"| GitHub | [{ORG}/{repo_name}]({repo_url})  |",
    ]
    if gitcode_url:
        lines. append(f"| GitCode | [{GITCODE_ORG}/{repo_nam e}]({gitcode_url}) |")
    lines += [
         f"| 类型 | {repo_type}（{level} 级） |" ,
        f"| 许可证 | {license_name} |",
         f"| 初始化 | {init_count} 项 |",
         f"| 可见性 | {visibility} |",
     ]
    comment = "\n".join(lines)

    api("PO ST", f"/repos/{ORG}/repository-requests/issue s/{issue_number}/comments", "gh", {"body": co mment})
    api("POST", f"/repos/{ORG}/reposi tory-requests/issues/{issue_number}/labels",  "gh", {"labels": ["status/completed"]})
    a pi("PATCH", f"/repos/{ORG}/repository-request s/issues/{issue_number}", "gh", {"state": "cl osed"})

    notify_feishu(repo_name, repo_ty pe, repo_url, author)

    print("Done.")


i f __name__ == "__main__":
    main()
 