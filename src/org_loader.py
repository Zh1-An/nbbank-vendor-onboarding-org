# -*- coding: utf-8 -*-
"""宁波银行合作方交付中心清单加载与校验。

校验项：二级组是否在白名单内、工号格式（NB + 5 位数字）、内线是否 4 位、邮箱是否已脱敏。
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from typing import Dict, List

CLIENT_NAME = "宁波银行"
ORG_ROOT = "宁波银行-合作方交付中心"
DEPARTMENTS = (
    "核心交付组",
    "支付交付组",
    "数据交付组",
    "运维值班组",
    "质量保障组",
)
ROLE_ALLOW = (
    "项目经理",
    "开发工程师",
    "数据工程师",
    "运维工程师",
    "值班经理",
    "质量工程师",
)
STAFF_NO = re.compile(r"^NB\d{5}$")
EXT_NO = re.compile(r"^\d{4}$")
MASKED_MAIL = re.compile(r"^[A-Za-z0-9]{3}\*{3}@[A-Za-z0-9.-]+$")


def load(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        if row.get("客户") != CLIENT_NAME:
            raise ValueError("清单混入其他客户：%s" % row.get("客户"))
    return rows


def validate(rows: List[Dict[str, str]]) -> List[str]:
    warnings: List[str] = []
    for idx, row in enumerate(rows, start=2):
        if row["二级组"] not in DEPARTMENTS:
            warnings.append("第 %d 行 组名不在白名单：%s" % (idx, row["二级组"]))
        if row["岗位"] not in ROLE_ALLOW:
            warnings.append("第 %d 行 岗位未知：%s" % (idx, row["岗位"]))
        if not STAFF_NO.match(row["工号"]):
            warnings.append("第 %d 行 工号格式不符：%s" % (idx, row["工号"]))
        if not EXT_NO.match(row["内线"]):
            warnings.append("第 %d 行 内线非 4 位：%s" % (idx, row["内线"]))
        if not MASKED_MAIL.match(row["邮箱"]):
            warnings.append("第 %d 行 邮箱未按规范脱敏：%s" % (idx, row["邮箱"]))
    return warnings


def summary(rows: List[Dict[str, str]]) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = defaultdict(list)
    for row in rows:
        groups[row["二级组"]].append("%s(%s)" % (row["姓名"], row["岗位"]))
    return groups


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("用法: python src/org_loader.py org/delivery-roster.csv")
        return 2
    rows = load(argv[1])
    warnings = validate(rows)
    print("%s / %s 共 %d 人" % (CLIENT_NAME, ORG_ROOT, len(rows)))
    for group, members in summary(rows).items():
        print("  %s: %d 人 -> %s" % (group, len(members), ", ".join(members)))
    oncall = [r["姓名"] for r in rows if r["二级组"] == "运维值班组"]
    print("值班联系人: %s" % ", ".join(oncall))
    if warnings:
        for line in warnings:
            print("WARN " + line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
