# -*- coding: utf-8 -*-
import base64, io, os
from PIL import Image

BASE = r"d:\桌面\我的文件\华大政国\青年发展部"
OUT = os.path.join(BASE, "青年发展部官网", "index.html")
TPL = os.path.join(BASE, "青年发展部官网", "template.html")

# (source, max_width, jpeg_quality)
SOURCES = {
    "IMG_LOGO": (r"2025-2026年度青年发展部部委\2025.10青马培训\政国logo.png", 640, 85),
    "IMG_MEMBER_LZ": (r"2026-2027年度青年发展部部长\青年发展部证件照\团委副书记李梓妍.png", 520, 82),
    "IMG_MEMBER_HXJ": (r"2026-2027年度青年发展部部长\青年发展部证件照\青年发展部部长黄晰嘉.jpg", 520, 82),
    "IMG_MEMBER_LZY": (r"2026-2027年度青年发展部部长\青年发展部证件照\青年发展部副部长黎芷悠.jpeg", 520, 82),
    "IMG_MEMBER_LMY": (r"2026-2027年度青年发展部部长\青年发展部证件照\青年发展部副部长罗梦语.jpg", 520, 82),
    "IMG_ACT_RUTUAN25": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\2025年入团积极分子联合培训.jpg", 1200, 76),
    "IMG_ACT_RUTUAN26": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\2026年入团积极分子联合培训.jpg", 1200, 76),
    "IMG_ACT_QINGMA": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\2025年“青马工程”培训班.jpg", 1200, 76),
    "IMG_ACT_FUNENG": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\第8期共青团改革创新赋能荟.png", 1200, 76),
    "IMG_ACT_RUDANG": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\汇总入党申请人信息.jpg", 1200, 76),
    "IMG_ACT_TUANJIAN": (r"2026-2027年度青年发展部部长\迎新工作\招新图片\活动图片\部门团建活动.jpg", 1200, 76),
}

def to_data_uri(path, max_w, quality):
    im = Image.open(os.path.join(BASE, path))
    if im.width > max_w:
        h = int(im.height * max_w / im.width)
        im = im.resize((max_w, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return "data:image/jpeg;base64," + b64

data = {}
total = 0
for key, (src, w, q) in SOURCES.items():
    uri = to_data_uri(src, w, q)
    data[key] = uri
    total += len(uri)
    print(key, "->", round(len(uri) / 1024), "KB")

with open(TPL, encoding="utf-8") as f:
    html = f.read()

for key, uri in data.items():
    html = html.replace("__" + key + "__", uri)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("FINAL SIZE:", round(os.path.getsize(OUT) / 1024 / 1024, 2), "MB")
