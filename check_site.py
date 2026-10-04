# -*- coding: utf-8 -*-
"""
青年发展部官网 · 站点自检脚本
------------------------------------------------
检查项：
  1. 每个页面引用的 data-asset 键是否都能在 js/assets-data.js 中找到；
  2. 站内相对链接 / 图片 / 样式 / 脚本的目标文件是否存在；
  3. 页面是否都带有统一的头部、导航、页脚与脚本引用；
  4. 导航链接与页面文件是否一一对应；
  5. 标签嵌套的几个高风险写法（figure 套 figure、标签交叉闭合）。

用法：
    python check_site.py
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

PAGES = [
    "index.html", "about.html", "organization.html", "activities.html",
    "news.html", "notices.html", "guide.html",
    "members.html", "contact.html",
]

errors = []
warnings = []
notes = []


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ---------- 载入资源映射 ----------
assets_js = os.path.join(BASE, "js", "assets-data.js")
if not os.path.exists(assets_js):
    print("!! 缺少 js/assets-data.js，请先运行 build_assets.py")
    sys.exit(1)

m = re.search(r"window\.DSH_ASSETS\s*=\s*(\{.*\});", read(assets_js), re.S)
if not m:
    print("!! 无法解析 js/assets-data.js 中的资源映射")
    sys.exit(1)
asset_map = json.loads(m.group(1))
notes.append("资源映射：%d 个图片键" % len(asset_map))

# ---------- 逐页检查 ----------
for page in PAGES:
    path = os.path.join(BASE, page)
    if not os.path.exists(path):
        errors.append("缺少页面文件：%s" % page)
        continue
    html = read(path)
    rel = page

    # 1. data-asset 键
    for key in set(re.findall(r'data-asset(?:-bg)?="([^"]+)"', html)):
        if key not in asset_map:
            errors.append("%s：data-asset 键未在资源映射中：%s" % (rel, key))

    # data-asset 元素必须有 src 兜底
    for tag in re.findall(r"<(?:img|div)[^>]*data-asset(?:-bg)?=[^>]*>", html):
        if "data-asset-bg" not in tag and "src=" not in tag:
            warnings.append("%s：data-asset 元素缺少 src 兜底：%s" % (rel, tag[:90]))

    # 2. 链接目标
    for href in re.findall(r'(?:href|src)="([^"]+)"', html):
        if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
            continue
        target = href.split("#")[0].split("?")[0]
        if not target:
            continue
        resolved = os.path.normpath(os.path.join(BASE, target))
        if not os.path.exists(resolved):
            errors.append("%s：链接目标不存在：%s" % (rel, href))

    # 3. 统一结构
    for needle, desc in [
        ('<nav class="mainnav"', "主导航"),
        ('class="site-header"', "站头"),
        ('class="site-footer"', "页脚"),
        ('js/main.js', "主脚本"),
        ('js/assets-data.js', "资源脚本"),
        ('id="toTop"', "返回顶部按钮"),
        ('id="today"', "日期占位"),
    ]:
        if needle not in html:
            errors.append("%s：缺少%s（%s）" % (rel, desc, needle))

    # 4. 导航项与页面文件对应
    for link in re.findall(r'class="nav-link[^"]*"\s+href="([^"]+)"', html):
        target = link.split("#")[0]
        if target and not os.path.exists(os.path.join(BASE, target)):
            errors.append("%s：导航链接目标不存在：%s" % (rel, link))

    # 每个页面只应有一个 active 导航项
    actives = len(re.findall(r'class="nav-link active"', html))
    if actives != 1:
        errors.append("%s：active 导航项数量异常（%d）" % (rel, actives))

    # 5. 高风险标签嵌套
    if re.search(r"<figure[^>]*>(?:(?!</figure>).)*<figure", html, re.S):
        errors.append("%s：存在 figure 嵌套 figure" % rel)
    if html.count("<figure") != html.count("</figure>"):
        errors.append("%s：figure 标签数量不匹配（%d/%d）" % (rel, html.count("<figure"), html.count("</figure>")))
    if html.count("<div") != html.count("</div>"):
        errors.append("%s：div 标签数量不匹配（%d/%d）" % (rel, html.count("<div"), html.count("</div>")))
    if html.count("<table") != html.count("</table>"):
        errors.append("%s：table 标签数量不匹配" % rel)
    if html.count("<section") != html.count("</section>"):
        errors.append("%s：section 标签数量不匹配（%d/%d）" % (rel, html.count("<section"), html.count("</section>")))
    if html.count("<ul") != html.count("</ul>"):
        errors.append("%s：ul 标签数量不匹配" % rel)

    # 站内锚点
    anchors = set(re.findall(r'id="([^"]+)"', html))
    for href in re.findall(r'href="#([^"]+)"', html):
        if href not in anchors:
            warnings.append("%s：页内锚点不存在：#%s" % (rel, href))

# ---------- 跨页锚点 ----------
for page in PAGES:
    html = read(os.path.join(BASE, page))
    for link in re.findall(r'href="([^"#]+\.html)#([^"]+)"', html):
        target, anchor = link
        tpath = os.path.join(BASE, target)
        if os.path.exists(tpath) and ('id="%s"' % anchor) not in read(tpath):
            errors.append("%s：跨页锚点不存在：%s#%s" % (page, target, anchor))

# ---------- CSS / JS 引用完整性 ----------
for page in PAGES:
    html = read(os.path.join(BASE, page))
    if 'href="css/style.css' not in html:
        errors.append("%s：未引用 css/style.css" % page)

print("=" * 66)
print("站点自检报告")
print("=" * 66)
for n in notes:
    print("  - %s" % n)
print("-" * 66)
if errors:
    print("错误 %d 项：" % len(errors))
    for e in errors:
        print("  [X] %s" % e)
else:
    print("错误 0 项 [OK]")
if warnings:
    print("提示 %d 项：" % len(warnings))
    for w in warnings:
        print("  [!] %s" % w)
else:
    print("提示 0 项 [OK]")
print("-" * 66)
print("页面数：%d    错误：%d    提示：%d" % (len(PAGES), len(errors), len(warnings)))
sys.exit(1 if errors else 0)
