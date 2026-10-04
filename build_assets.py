# -*- coding: utf-8 -*-
"""
青年发展部官网 · 图片素材处理脚本
------------------------------------------------
把部门现有图片压缩后转成 data URI，写入 js/assets-data.js，
使整站可以离线双击打开、也可直接上传到任意静态服务器。

用法：
    python build_assets.py
"""
import base64
import io
import json
import os
import sys

from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)          # 部门根目录：D:\桌面\我的文件\华大政国\青年发展部
OUT_JS = os.path.join(BASE, "js", "assets-data.js")

# key: (相对部门根目录的源文件, 最大宽度, JPEG 质量, 是否保留 PNG 透明)
SOURCES = {
    # 标识
    "IMG_LOGO": (r"2025-2026年度青年发展部部委\2025.10青马培训\政国logo.png", 460, 90, True),
    # 成员证件照
    "IMG_MEMBER_LZY": (r"2026-2027年度青年发展部部长\青年发展部证件照\团委副书记李梓妍.png", 620, 84, False),
    "IMG_MEMBER_HXJ": (r"2026-2027年度青年发展部部长\青年发展部证件照\青年发展部部长黄晰嘉.jpg", 620, 84, False),
    "IMG_MEMBER_LZY2": (r"2026-2027年度青年发展部部长\青年发展部证件照\青年发展部副部长黎芷悠.jpeg", 620, 84, False),
    "IMG_MEMBER_LMY": (r"2026-2027年度青年发展部部长\青年发展部证件照\青年发展部副部长罗梦语.jpg", 620, 84, False),
    # 横幅背景（宽幅、压暗后不影响文字）
    "IMG_HERO": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\部门团建活动.jpg", 1600, 70, False),
    # 活动照片
    "IMG_ACT_TUANJIAN": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\部门团建活动.jpg", 1200, 74, False),
    "IMG_ACT_RUTUAN25": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\2025年入团积极分子联合培训.jpg", 1200, 74, False),
    "IMG_ACT_QINGMA": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\2025年“青马工程”培训班.jpg", 1200, 74, False),
    "IMG_ACT_FUNENG": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\第8期共青团改革创新赋能荟.png", 1200, 74, False),
    "IMG_ACT_RUDANG": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\汇总入党申请人信息.jpg", 1200, 74, False),
    "IMG_ACT_RUTUAN26": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\2026年入团积极分子联合培训.jpg", 1200, 74, False),
    # 招新海报（竖版，单独缩放）
    "IMG_POSTER": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\ZGQNFZB (1440 x 2560 像素).png", 760, 78, False),
}


def to_data_uri(path, max_w, quality, keep_alpha):
    img = Image.open(path)
    if img.width > max_w:
        h = max(1, int(round(img.height * max_w / img.width)))
        img = img.resize((max_w, h), Image.LANCZOS)

    buf = io.BytesIO()
    if keep_alpha:
        img = img.convert("RGBA")
        img.save(buf, "PNG", optimize=True)
        mime = "image/png"
    else:
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            rgba = img.convert("RGBA")
            bg.paste(rgba, mask=rgba.split()[-1])
            img = bg
        else:
            img = img.convert("RGB")
        img.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
        mime = "image/jpeg"
    return "data:%s;base64,%s" % (mime, base64.b64encode(buf.getvalue()).decode("ascii"))


def main():
    data = {}
    total = 0
    missing = []

    for key in sorted(SOURCES):
        rel, max_w, quality, keep_alpha = SOURCES[key]
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            missing.append((key, rel))
            print("  [缺失] %-18s %s" % (key, rel))
            continue
        try:
            uri = to_data_uri(src, max_w, quality, keep_alpha)
        except Exception as exc:                       # noqa: BLE001
            missing.append((key, rel))
            print("  [失败] %-18s %s -> %s" % (key, rel, exc))
            continue
        data[key] = uri
        total += len(uri)
        print("  %-18s -> %6.1f KB" % (key, len(uri) / 1024.0))

    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    lines = [
        "/* 本文件由 build_assets.py 自动生成，请勿手工修改。 */",
        "/* 图片已压缩并以 data URI 内嵌，保证离线打开与整目录迁移均不丢图。 */",
        "window.DSH_ASSETS = " + payload + ";",
        "",
        "(function () {",
        "  var map = window.DSH_ASSETS;",
        "  if (!map) { return; }",
        "  function swap() {",
        "    var nodes = document.querySelectorAll('[data-asset]');",
        "    for (var i = 0; i < nodes.length; i++) {",
        "      var key = nodes[i].getAttribute('data-asset');",
        "      if (map[key]) { nodes[i].setAttribute('src', map[key]); }",
        "    }",
        "    var bgNodes = document.querySelectorAll('[data-asset-bg]');",
        "    for (var j = 0; j < bgNodes.length; j++) {",
        "      var bkey = bgNodes[j].getAttribute('data-asset-bg');",
        "      if (map[bkey]) { bgNodes[j].style.backgroundImage = 'url(' + map[bkey] + ')'; }",
        "    }",
        "  }",
        "  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', swap); }",
        "  else { swap(); }",
        "})();",
        "",
    ]

    os.makedirs(os.path.dirname(OUT_JS), exist_ok=True)
    with open(OUT_JS, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print("-" * 62)
    print("已写入：%s" % OUT_JS)
    print("图片数量：%d    合计：%.2f MB" % (len(data), total / 1024.0 / 1024.0))
    if missing:
        print("未处理的源图：%s" % ", ".join("%s(%s)" % m for m in missing))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
