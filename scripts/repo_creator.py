#!/usr/bin/env python3
"""
huaweicloud-mate � ��箔��箏鈭?�?�?GOAT 撱箔�� ���﹝ v1.1
�舀� 9 蝘�� �掩�?�?4 銝芰�蝥批�憪�� ��?~14 憿對�
"""

import json, os, re, ti me
import urllib.request, urllib.error

ORG =  os.environ.get("ORG_NAME", "huaweicloud-mate ")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "" )
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN ", "")
EVENT_PATH = os.environ.get("GITHUB_EV ENT_PATH", "")

GITCODE_ORG = os.environ.get( "GITCODE_ORG", "hd-vector")
GITCODE_USERNAME  = os.environ.get("GITCODE_USERNAME", "")
GITC ODE_TOKEN = os.environ.get("GITCODE_TOKEN", " ")

FEISHU_APP_ID = os.environ.get("FEISHU_AP P_ID", "")
GITCODE_API = "https://gitcode.com /api/v5"
GC_HEADERS = {"PRIVATE-TOKEN": GITCO DE_TOKEN, "Content-Type": "application/json"} 

FEISHU_APP_ID = os.environ.get("FEISHU_APP_ ID", "")
FEISHU_APP_SECRET = os.environ.get(" FEISHU_APP_SECRET", "")
FEISHU_ADMIN_OPEN_ID  = os.environ.get("FEISHU_ADMIN_OPEN_ID", "")
 
GITHUB_API = "https://api.github.com"
BOT_HE ADERS = {"Authorization": f"Bearer {BOT_TOKEN }", "Accept": "application/vnd.github+json"}
 GH_HEADERS = {"Authorization": f"Bearer {GITH UB_TOKEN}", "Accept": "application/vnd.github +json"}

# ��� 蝐餃��� 蝥扳�撠?���
PRODUCT_TYPES =  ["SDK", "Terraform Provider", "GitHub Action" , "獢��", "Exporter / Plugin",  "IoT SDK"]
SAMPLE_TYPES = ["蝷箔� / Lab /  Sample"]
DOCS_TYPES = ["�﹝ / �唳� ��?]
INTERNAL_TYPES = ["��蔭" ]


def api(method, path, token=None, data=No ne):
    headers = BOT_HEADERS if token == "b ot" else GH_HEADERS
    url = f"{GITHUB_API}{ path}"
    body = json.dumps(data).encode() i f data else None
    req = urllib.request.Req uest(url, data=body, headers=headers, method= method)
    try:
        with urllib.request. urlopen(req, timeout=30) as resp:
             if resp.status == 204:
                retur n None
            return json.loads(resp.rea d())
    except urllib.error.HTTPError as e:
         err = e.read().decode()[:500]
         print(f"API {method} {path}: {e.code} {err}" )
        return None


def load_event():
     with open(EVENT_PATH) as f:
        return j son.load(f)


def gitcode_api(method, path, d ata=None):
    """靚 GitCode API嚗 itLab �澆捆嚗?""
    if not GITCODE_TOKE N:
        print("GITCODE_TOKEN not set, skip ping GitCode API")
        return None
    ur l = f"{GITCODE_API}{path}"
    body = json.du mps(data).encode() if data else None
    req  = urllib.request.Request(url, data=body, head ers=GC_HEADERS, method=method)
    try:
         with urllib.request.urlopen(req, timeout=3 0) as resp:
            if resp.status == 204 :
                return None
            ret urn json.loads(resp.read())
    except urllib .error.HTTPError as e:
        err = e.read() .decode()[:500]
        print(f"GitCode API { method} {path}: {e.code} {err}")
        retu rn None


def create_gitcode_repo(repo_name,  description):
    """�?GitCode 銝�撱 箏���摨?""
    # �瑕� hd-vect or group �?ID
    group_url = f"/groups/{GI TCODE_ORG}"
    group = gitcode_api("GET", gr oup_url)
    if not group or "id" not in grou p:
        print(f"Failed to get GitCode grou p {GITCODE_ORG}")
        return None

    na mespace_id = group["id"]
    data = {
         "name": repo_name,
        "path": repo_name ,
        "namespace_id": namespace_id,
         "description": description or "",
         "visibility": "public",
        "initialize_w ith_readme": False,
    }
    result = gitcod e_api("POST", "/projects", data)
    if resul t and "id" in result:
        gitcode_url = r esult.get("web_url", f"https://gitcode.com/{G ITCODE_ORG}/{repo_name}")
        print(f"Git Code repo created: {gitcode_url}")
        re turn gitcode_url
    print(f"Failed to create  GitCode repo")
    return None


# ��� �� 霈詨霂��?���
 def get_license(repo_type, user_choice):
     if repo_type in PRODUCT_TYPES:
        choice _map = {"Apache-2.0嚗��": "Apac he-2.0", "Apache-2.0": "Apache-2.0", "MIT": " MIT", "BSD-3-Clause": "BSD-3-Clause"}
         return choice_map.get(user_choice, "Apache-2 .0")
    return "Apache-2.0"


# ��� � README 璅⊥嚗?憟� ��� ��
README_TEMPLATES = {
    "SDK": """# {na me}
[![License](https://img.shields.io/badge/ License-{license}-blue.svg)](LICENSE)

{descr iption}

## 摰�
```bash
pip install {na me}
```

## API �?
敺‘�?

## � ��∠
�亦� [CONTRIBUTING.md](CONTRIBU TING.md)

## 霈詨霂?
�祇★�桐蝙 �?{license} 霈詨霂?
""",
    "Te rraform Provider": """# {name}
[![License](ht tps://img.shields.io/badge/License-{license}- blue.svg)](LICENSE)

{description}

## Provid er �蔭
```hcl
provider "{name}" {{
  #  �蔭憿?
}}
```

## Resource / DataSourc e �”
敺‘�?

## 韐∠
�� �� [CONTRIBUTING.md](CONTRIBUTING.md)
""",
     "GitHub Action": """# {name}
[![License]( https://img.shields.io/badge/License-{license }-blue.svg)](LICENSE)

{description}

## Inpu ts
| � | 蝐餃� | 敹� | 暺� ��恕�?| 霂湔� |
|------|------|------| --------|------|

## Outputs
| 颲 | � �湔� |
|------|------|

## 雿輻蝷箔 �
```yaml
- uses: huaweicloud-mate/{name}@v 1
  with:
    param: value
```

## 韐∠
 �亦� [CONTRIBUTING.md](CONTRIBUTING.md)
 """,
    "獢��": """# {name}
[! [License](https://img.shields.io/badge/Licens e-{license}-blue.svg)](LICENSE)

{description }

## 敹恍��?
```bash
pip install  {name}
```

## �蔭霂湔�
敺‘� �?

## ��澆捆
| � | �� �捆霂剛� / 獢 | �嗆?|
|----- -|----------------|------|

## 韐∠
�� ��� [CONTRIBUTING.md](CONTRIBUTING.md)
""", 
    "Exporter / Plugin": """# {name}
[![Lice nse](https://img.shields.io/badge/License-{li cense}-blue.svg)](LICENSE)

{description}

##  �函蔡�孵�
```bash
docker run -d --n ame {name} huaweicloud-mate/{name}:latest
``` 

## ��霂湔�
敺‘�?

## 韐 ∠
�亦� [CONTRIBUTING.md](CONTRIBUTI NG.md)
""",
    "IoT SDK": """# {name}
[![Lic ense](https://img.shields.io/badge/License-{l icense}-blue.svg)](LICENSE)

{description}

# # 蝖砌辣閬�
敺‘�?

## 霈曉 ��亙蝷箔�
```python
from {name} i mport Device
device = Device("device-id")
dev ice.connect()
```

## 韐∠
�亦� [CO NTRIBUTING.md](CONTRIBUTING.md)
""",
    "蝷 箔� / Lab / Sample": """# {name}

{descrip tion}

## �蔭�∩辣
- 霂剛��� ��
- 靘�摰�

## 餈�甇仿 炊
```bash
# 餈�蝷箔�
```

## �� ���撅內
敺‘�?
""",
    "� ﹝ / �唳�?: """# {name}

{descriptio n}

## �捆霂湔�
敺‘�?

## � ��輻�孵�
敺‘�?
""",
    "� �蔭": """# {name}

{description}
 
> ��蔭隞�

## �券?
 敺‘�?

## 雿輻�孵�
敺� ��?
""",
}


def make_readme(name, repo_typ e, license_name, description):
    tmpl = REA DME_TEMPLATES.get(repo_type, README_TEMPLATES ["SDK"])
    return tmpl.format(name=name, li cense=license_name, description=description)
 

# ��� �辣璅⊥ �� ���
CONTRIBUTING_MD = """# Contributing  to {name}

## 撘�憓撱?
� �?README�?

## �漱閫�
雿輻 蝥血�撘�鈭歹�`feat:`, `fix:`, ` docs:`, `style:`, `refactor:`, `test:`, `chor e:`

## PR 瘚�
1. Fork 隞�
2. � 遣� `feat/xxx`
3. �漱隞� �
4. �絲 Pull Request
5. �喳� 2  鈭?Review + CI ����撟?

## Is sue 閫�
雿輻 Bug Report / Feature  Request 璅⊥
"""

SECURITY_MD = """# Sec urity Policy

## �亙�摰瞍�
 憒��啣��冽�瘣�霂瑕� �隞嗉 security@huaweicloud-mate. dev嚗?*銝��典撘 Issue 銝剜� ���?*�?

## �舀��
| �� � | �舀��嗆?|
|------|---------|
|  ��?| �?瘣餉��舀� |
"""

COC_ MD = """# Contributor Covenant Code of Conduc t

## �賑�霂?
銝箔��仿� ��銝芸��曉��末�� ���賑�輯笑撠��� �銝?

## �賑���?
 - 雿輻�末��摰寧�霂剛� ��
- 撠�銝����孵�蝏� ���
- 撱箄挽�批�亙��寡�
 
## �扯�
餈�銵蛹�舀�� ��憿寧蝏湔�?
"""

BUG_REP ORT_YML = """name: Bug Report
description: � �亙�銝銝?bug
labels: ["type/bug"]
body :
  - type: textarea
    attributes:
      la bel: �膩
      description: ��� ��銋?
    validations:
      required:  true
  - type: textarea
    attributes:
       label: 憭甇仿炊
  - type: textarea 
    attributes:
      label: ��銵 蛹
  - type: textarea
    attributes:
       label: �臬�靽⊥
"""

FEATURE_YML =  """name: Feature Request
description: 霂瑟� ��銝銝芣�
labels: ["type/feat ure"]
body:
  - type: textarea
    attributes :
      label: �膩
      description: � ����溶��銋��?
    v alidations:
      required: true
  - type: te xtarea
    attributes:
      label: 雿輻 �箸
"""

CONFIG_YML = """blank_issues_e nabled: false
"""

PR_TEMPLATE = """## � 霂湔�


## �唾� Issue
Fixes #

##  瘚�
- [ ] ��瘚���
 - [ ] �瘚���
"""

TRIAGE _WORKFLOW = """name: Issue Triage
on:
  issue s:
    types: [opened]
permissions:
  issues:  write
  contents: read
jobs:
  triage:
    r uns-on: ubuntu-latest
    steps:
      - uses : huaweicloud-mate/.github/actions/issue-bot@ main
        env:
          GITHUB_TOKEN: ${{  secrets.GITHUB_TOKEN }}
"""

SYNC_WORKFLOW =  f"""name: Sync to GitCode
on:
  push:
    br anches: [main]
permissions:
  contents: read
 jobs:
  sync:
    runs-on: ubuntu-latest
     steps:
      - uses: actions/checkout@v4
         with:
          fetch-depth: 0
      - ru n: |
          git remote add gitcode https:/ /{GITCODE_USERNAME}:${{{{ secrets.GITCODE_TOK EN }}}}@gitcode.com/{GITCODE_ORG}/${{{{ githu b.event.repository.name }}}}.git || true
           git push gitcode main --force
"""

DEPE NDABOT = """version: 2
updates:
  - package-e cosystem: "github-actions"
    directory: "/" 
    schedule:
      interval: "weekly"
"""

 LABELS_PRODUCT = ["type/bug", "type/enhanceme nt", "type/question", "type/documentation",
                   "priority/critical", "priori ty/high", "priority/medium", "priority/low",
                   "status/pending", "status/i n-progress", "status/blocked",
                   "good first issue", "help wanted", "agent /triaged"]
LABELS_SAMPLE = LABELS_PRODUCT[:8] 


def create_file(repo, path, content, messa ge):
    api("PUT", f"/repos/{ORG}/{repo}/con tents/{path}", "bot", {"message": message, "c ontent": b64(content)})


def b64(s):
    imp ort base64
    return base64.b64encode(s.enco de()).decode()


def create_labels(repo, labe ls):
    for name in labels:
        api("POS T", f"/repos/{ORG}/{repo}/labels", "bot", {"n ame": name, "color": "ededed"})


def validat e_repo_name(name):
    return bool(re.match(r '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', name)) and  len(name) <= 100


def validate_topics(topic s_str):
    topics = re.split(r'[,\n]+', topi cs_str.strip())
    valid = []
    for t in t opics:
        t = t.strip().lower()
         if re.match(r'^[a-z0-9][a-z0-9.-]*$', t):
             valid.append(t)
    return valid


d ef assign_role(repo, role, users):
    if not  users:
        return
    role_map = {"owner ": "admin", "maintainer": "maintain", "writer ": "push"}
    perm = role_map.get(role, "pus h")
    for user in users:
        api("PUT",  f"/repos/{ORG}/{repo}/collaborators/{user}",  "bot", {"permission": perm})


def notify_fe ishu(repo_name, repo_type, url, author):
     if not all([FEISHU_APP_ID, FEISHU_APP_SECRET,  FEISHU_ADMIN_OPEN_ID]):
        return
    t ry:
        token_resp = json.loads(urllib.re quest.urlopen(
            urllib.request.Req uest("https://open.feishu.cn/open-apis/auth/v 3/tenant_access_token/internal",
                                    data=json.dumps({"app_ id": FEISHU_APP_ID, "app_secret": FEISHU_APP_ SECRET}).encode(),
                                    headers={"Content-Type": "applicatio n/json"}), timeout=10).read())
        token  = token_resp.get("tenant_access_token", "")
         if not token:
            return

         card = {
            "config": {"wide_scr een_mode": True},
            "header": {"tit le": {"tag": "plain_text", "content": "  隞� ����遣��"}, "template": "turqu oise"},
            "elements": [
                 {"tag": "markdown", "content": f"**{auth or}** �唾窈��摨歇�遣"}, 
                {"tag": "div", "fields": [
                     {"is_short": True, "text":  {"tag": "lark_md", "content": f"**隞�� ��妍**\n{repo_name}"}},
                     {"is_short": True, "text": {"tag": "lark_m d", "content": f"**蝐餃�**\n{repo_type}"} },
                ]},
                {"tag" : "action", "actions": [
                     {"tag": "button", "text": {"tag": "plain_text ", "content": "�亦�隞�"}, "type":  "primary", "url": url},
                ]},
                 {"tag": "note", "elements": [{ "tag": "plain_text", "content": "huaweicloud- mate Repo Creator"}]}
            ]
        } 
        urllib.request.urlopen(urllib.reques t.Request(
            f"https://open.feishu. cn/open-apis/im/v1/messages?receive_id_type=o pen_id",
            data=json.dumps({"receiv e_id": FEISHU_ADMIN_OPEN_ID, "msg_type": "int eractive",
                             "cont ent": json.dumps(card, ensure_ascii=False)}). encode(),
            headers={"Authorization ": f"Bearer {token}", "Content-Type": "applic ation/json"}), timeout=10)
        print("Fei shu notification sent")
    except Exception  as e:
        print(f"Feishu notification fai led: {e}")


def get_init_level(repo_type):
     if repo_type in PRODUCT_TYPES:
        ret urn "product"
    elif repo_type in SAMPLE_TY PES:
        return "sample"
    elif repo_ty pe in DOCS_TYPES:
        return "docs"
    e lse:
        return "internal"


def main():
     event = load_event()
    issue = event.ge t("issue", {})
    issue_number = issue.get(" number", 0)
    labels = [l["name"] for l in  issue.get("labels", [])]
    title = issue.ge t("title", "")

    if "status/approved" not  in labels:
        print("Not approved, skipp ing")
        return

    body = issue.get("b ody", "")
    author = issue.get("user", {}). get("login", "")

    # parse form fields (se ction header -> next line is value)
    lines  = body.split("\n")
    fields = {}
    for i , line in enumerate(lines):
        for prefi x in ["### 隞�蝐餃�", "### 隞� ��妍", "### 隞��膩", "### � ��航��?,
                        "### � �皞捂�航�", "### Topics �倌 ", "### Owner", "### Maintainer",
                         "### Writer", "### �唾窈�� ��"]:
            if line.startswith(prefi x):
                key = prefix.replace("###  ", "").strip()
                # value is on  the next non-empty line
                for  j in range(i + 1, min(i + 3, len(lines))):
                     val = lines[j].strip()
                     if val and not val.startswith ("###") and not val.startswith("_"):
                         fields[key] = val
                         break
                break

     repo_type = fields.get("隞�蝐餃�",  "SDK")
    repo_name = fields.get("隞� �妍", "").strip().lower()
    descripti on = fields.get("隞��膩", "")
     visibility = fields.get("�航��?, "pub lic").lower()
    license_choice = fields.get ("撘皞捂�航�", "Apache-2.0")
     topics_raw = fields.get("Topics �倌",  "")
    owner_str = fields.get("Owner", "")
     maintainer_str = fields.get("Maintainer",  "")
    writer_str = fields.get("Writer", "") 
    justification = fields.get("�唾窈� ", "")

    print(f"Processing Issue #{ issue_number}: {title}")
    print(f"Type: {r epo_type}, Name: {repo_name}")

    if not va lidate_repo_name(repo_name):
        api("POS T", f"/repos/{ORG}/repository-requests/issues /{issue_number}/comments", "gh",
             {"body": f"  **隞��妍�澆�� 秤**嚗{repo_name}` 銝泵�� ��撠�摮�+�啣�+餈� ��蝚佗��?00摮泵嚗?})
        retu rn

    topics = validate_topics(topics_raw)
     if len(topics) < 3:
        api("POST", f "/repos/{ORG}/repository-requests/issues/{iss ue_number}/comments", "gh",
            {"bod y": f"  **Topics 銝雲**嚗撠� �閬?3 銝芸�瘜�蝑橘�敶� { len(topics)} 銝迎�"})
        return

     # check duplicate
    existing = api("GET",  f"/repos/{ORG}/{repo_name}", "bot")
    if ex isting and "id" in existing:
        api("POS T", f"/repos/{ORG}/repository-requests/issues /{issue_number}/comments", "gh",
             {"body": f"  **隞�撌脣��?*嚗{ ORG}/{repo_name}` 撌脣��?})
        ret urn

    license_name = get_license(repo_type , license_choice)
    level = get_init_level( repo_type)

    # create repo
    create_data  = {
        "name": repo_name,
        "desc ription": description,
        "private": vis ibility == "private",
        "auto_init": Tr ue,
        "has_issues": True,
        "has_ projects": False,
        "has_wiki": False,
         "allow_squash_merge": True,
        " allow_merge_commit": False,
        "allow_re base_merge": False,
    }
    result = api("P OST", f"/orgs/{ORG}/repos", "bot", create_dat a)
    if not result or "id" not in result:
         print(f"Failed to create repo: {result }")
        return

    repo_url = result["ht ml_url"]
    print(f"Repo created: {repo_url} ")

    # init files
    readme = make_readme (repo_name, repo_type, license_name, descript ion)
    create_file(repo_name, "README.md",  readme, "Init README")
    create_file(repo_n ame, "LICENSE", f"{license_name} License\n",  f"Add {license_name} license")

    if level  in ("product", "sample"):
        create_file (repo_name, "CONTRIBUTING.md", CONTRIBUTING_M D.format(name=repo_name), "Add contributing g uide")
    if level == "product":
        cre ate_file(repo_name, "SECURITY.md", SECURITY_M D, "Add security policy")
        create_file (repo_name, "CODE_OF_CONDUCT.md", COC_MD, "Ad d code of conduct")
    if level in ("product ", "sample"):
        create_file(repo_name,  ".github/ISSUE_TEMPLATE/bug_report.yml", BUG_ REPORT_YML, "Add bug template")
        creat e_file(repo_name, ".github/ISSUE_TEMPLATE/fea ture_request.yml", FEATURE_YML, "Add feature  template")
        create_file(repo_name, ".g ithub/ISSUE_TEMPLATE/config.yml", CONFIG_YML,  "Add issue config")
        create_file(repo _name, ".github/PULL_REQUEST_TEMPLATE.md", PR _TEMPLATE, "Add PR template")
    if level ==  "product":
        create_file(repo_name, ". github/dependabot.yml", DEPENDABOT, "Add depe ndabot config")
        create_file(repo_name , ".github/workflows/triage-issue.yml", TRIAG E_WORKFLOW, "Add triage workflow")
        cr eate_file(repo_name, ".github/workflows/sync- to-gitcode.yml", SYNC_WORKFLOW, "Add GitCode  sync workflow")

    # labels
    if level ==  "product":
        create_labels(repo_name,  LABELS_PRODUCT)
    elif level == "sample":
         create_labels(repo_name, LABELS_SAMPLE )

    # topics
    api("PUT", f"/repos/{ORG} /{repo_name}/topics", "bot",
        {"names" : topics[:20]})

    # roles
    owners = [u. strip() for u in re.split(r'[,\n]+', owner_st r) if u.strip()]
    maintainers = [u.strip()  for u in re.split(r'[,\n]+', maintainer_str)  if u.strip()]
    writers = [u.strip() for u  in re.split(r'[,\n]+', writer_str) if u.stri p()]

    for u in owners:
        assign_rol e(repo_name, "owner", [u])
    for u in maint ainers:
        if u not in owners:
             assign_role(repo_name, "maintainer", [u])
     for u in writers:
        if u not in own ers and u not in maintainers:
            ass ign_role(repo_name, "writer", [u])

    # cre ate GitCode mirror
    gitcode_url = create_g itcode_repo(repo_name, description)

    # cl ose issue
    init_count = {"product": 14, "s ample": 7, "docs": 3, "internal": 2}[level]
     lines = [
        f"##  撱箔�摰� ",
        f"",
        f"| 憿寧 | 霂� �� |",
        f"|------|------|",
         f"| GitHub | [{ORG}/{repo_name}]({repo_url})  |",
    ]
    if gitcode_url:
        lines.a ppend(f"| GitCode | [{GITCODE_ORG}/{repo_name }]({gitcode_url}) |")
    lines += [
         f"| 蝐餃� | {repo_type}嚗level} 蝥� �� |",
        f"| 霈詨霂?| {license_ name} |",
        f"| ���?| {init_co unt} 憿?|",
        f"| �航��?| {visi bility} |",
    ]
    comment = "\n".join(lin es)

    api("POST", f"/repos/{ORG}/repositor y-requests/issues/{issue_number}/comments", " gh", {"body": comment})
    api("POST", f"/re pos/{ORG}/repository-requests/issues/{issue_n umber}/labels", "gh", {"labels": ["status/com pleted"]})
    api("PATCH", f"/repos/{ORG}/re pository-requests/issues/{issue_number}", "gh ", {"state": "closed"})

    notify_feishu(re po_name, repo_type, repo_url, author)

    pr int("Done.")


if __name__ == "__main__":
     main()
 