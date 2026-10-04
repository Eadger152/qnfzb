# -*- coding: utf-8 -*-
"""
把「青年发展部官网」目录通过 GitHub REST API 上传到仓库 qnfzb。
不依赖本地 git。用法：
    set GITHUB_TOKEN=xxx
    python push_to_github.py --dry-run   # 只列出将要上传的文件
    python push_to_github.py             # 真正上传
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
OWNER_REPO = "Eadger152/qnfzb"
BRANCH = "main"
API = "https://api.github.com"

# 不上传的内容（与 .gitignore 保持一致）
EXCLUDE_DIRS = {"_shots", "src", ".git", "__pycache__"}
EXCLUDE_FILES = {"single-page.html"}
EXCLUDE_EXT = {".pyc", ".tmp", ".bak"}

TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
DRY = "--dry-run" in sys.argv


def api(method, path, payload=None, raw=False):
    url = path if path.startswith("http") else API + path
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "dsh-uploader")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read()
            return resp.status, (body if raw else json.loads(body or b"{}"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        return exc.code, detail


def collect_files():
    out = []
    for root, dirs, files in os.walk(SITE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for name in files:
            if name in EXCLUDE_FILES:
                continue
            if os.path.splitext(name)[1].lower() in EXCLUDE_EXT:
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, SITE_DIR).replace("\\", "/")
            out.append((rel, full))
    out.sort()
    return out


def extra_files():
    """命令行以 --file=路径 形式额外指定要上传的文件（路径相对站点目录）。"""
    out = []
    for arg in sys.argv[1:]:
        if not arg.startswith("--file="):
            continue
        rel = arg.split("=", 1)[1].replace("\\", "/")
        full = os.path.join(SITE_DIR, rel)
        if os.path.exists(full):
            out.append((rel, full))
        else:
            print("!! 指定的文件不存在：%s" % rel)
    return out


def main():
    if not TOKEN:
        print("!! 未设置 GITHUB_TOKEN")
        return 1

    files = collect_files()
    skip = {"push_to_github.py"}
    files = [(r, f) for (r, f) in files if r not in skip]
    files += [(r, f) for (r, f) in extra_files() if r not in skip]
    files.sort()
    total = sum(os.path.getsize(p) for _, p in files)
    print("仓库：%s   分支：%s" % (OWNER_REPO, BRANCH))
    print("待上传：%d 个文件，共 %.2f MB" % (len(files), total / 1024.0 / 1024.0))
    for rel, full in files:
        print("   %8.1f KB  %s" % (os.path.getsize(full) / 1024.0, rel))
    if DRY:
        print("\n[dry-run] 未执行任何上传。")
        return 0

    # 1. 确保仓库存在
    code, body = api("GET", "/repos/" + OWNER_REPO)
    if code == 200:
        print("\n仓库已存在，直接推送。")
    elif code == 404:
        print("\n创建公开仓库 qnfzb ...")
        code, body = api("POST", "/user/repos", {
            "name": OWNER_REPO.split("/")[1],
            "description": "华中师范大学政治与国际关系学院团委 · 青年发展部官方网站",
            "homepage": "https://%s.github.io/%s/" % (OWNER_REPO.split("/")[0], OWNER_REPO.split("/")[1]),
            "private": False,
            "has_issues": True,
            "has_wiki": False,
            "auto_init": False,
        })
        if code not in (200, 201):
            print("!! 创建仓库失败 %s: %s" % (code, body))
            return 2
        print("仓库已创建。")
    else:
        print("!! 查询仓库失败 %s: %s" % (code, body))
        return 2

    # 2. 逐个文件建 blob
    print("\n上传文件（Git Data API）...")
    tree = []
    for rel, full in files:
        with open(full, "rb") as fh:
            content = base64.b64encode(fh.read()).decode("ascii")
        code, body = api("POST", "/repos/%s/git/blobs" % OWNER_REPO, {
            "content": content, "encoding": "base64",
        })
        if code not in (200, 201):
            print("!! blob 失败 %s %s: %s" % (rel, code, body))
            return 3
        tree.append({"path": rel, "mode": "100644", "type": "blob", "sha": body["sha"]})
        print("   ok  %s" % rel)
        time.sleep(0.05)

    # 3. 建 tree
    code, body = api("POST", "/repos/%s/git/trees" % OWNER_REPO, {"tree": tree})
    if code not in (200, 201):
        print("!! tree 失败 %s: %s" % (code, body))
        return 4
    tree_sha = body["sha"]
    print("tree: %s" % tree_sha)

    # 4. 建 commit（无父提交则为首个提交）
    code, ref = api("GET", "/repos/%s/git/ref/heads/%s" % (OWNER_REPO, BRANCH))
    payload = {
        "message": "青年发展部官网首次发布\n\n共 %d 个页面与素材，纯静态站点，可离线打开。\n" % len(files),
        "tree": tree_sha,
    }
    if code == 200:
        payload["parents"] = [ref["object"]["sha"]]
        print("基于已有分支提交。")
    code, body = api("POST", "/repos/%s/git/commits" % OWNER_REPO, payload)
    if code not in (200, 201):
        print("!! commit 失败 %s: %s" % (code, body))
        return 5
    commit_sha = body["sha"]
    print("commit: %s" % commit_sha)

    # 5. 创建 / 更新分支引用
    code, _ = api("GET", "/repos/%s/git/ref/heads/%s" % (OWNER_REPO, BRANCH))
    if code == 200:
        code, body = api("PATCH", "/repos/%s/git/refs/heads/%s" % (OWNER_REPO, BRANCH), {
            "sha": commit_sha, "force": True,
        })
    else:
        code, body = api("POST", "/repos/%s/git/refs" % OWNER_REPO, {
            "ref": "refs/heads/" + BRANCH, "sha": commit_sha,
        })
    if code not in (200, 201):
        print("!! 更新分支失败 %s: %s" % (code, body))
        return 6
    print("分支 %s 已指向新提交。" % BRANCH)

    # 6. 开启 GitHub Pages
    print("\n开启 GitHub Pages ...")
    code, body = api("POST", "/repos/%s/pages" % OWNER_REPO, {
        "source": {"branch": BRANCH, "path": "/"},
    })
    if code in (200, 201):
        print("Pages 已开启：%s" % body.get("html_url", ""))
    elif code == 409:
        code, body = api("PUT", "/repos/%s/pages" % OWNER_REPO, {
            "source": {"branch": BRANCH, "path": "/"},
        })
        print("Pages 已更新。" if code in (200, 204) else "Pages 返回 %s: %s" % (code, body))
    else:
        print("Pages 返回 %s: %s" % (code, body))

    print("\n完成。")
    print("仓库：https://github.com/%s" % OWNER_REPO)
    print("网站：https://%s.github.io/%s/" % (OWNER_REPO.split("/")[0], OWNER_REPO.split("/")[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
