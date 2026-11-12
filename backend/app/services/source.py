"""采集源管理业务规则：状态流转、字段校验与筛选口径都收在这里。"""
from __future__ import annotations

from typing import Any

from app.store import store

MODULE = "source"
REQUIRED_FIELDS = ["源端编号", "源端名称", "接入协议"]
OPTIONAL_FIELDS = ["目标地址", "认证方式", "字符编码", "连接超时", "负责人"]
STATUS_ORDER = ["草稿", "待校验", "已启用", "已停用"]
ACTION_RULES = {"提交校验": "待校验", "启用配置": "已启用", "停用配置": "已停用"}
NEGATIVE_ACTIONS = ["停用配置"]

# 多维定位字段，命中优先级：源端编号 > 源端名称 > 接入协议 > 负责人。
# 组合条件之间取并集：任一维度命中即返回，名称、协议、负责人可交叉定位。
DIMENSION_FIELDS = ["源端编号", "源端名称", "接入协议", "负责人"]


def _code_sort_key(value: Any) -> tuple[str, int, str]:
    """源端编号自然排序键：同前缀按数字段升序，保证同名记录按编号稳定排列。"""
    text = str(value or "")
    head, sep, tail = text.rpartition("-")
    if sep and tail.isdigit():
        return (head, int(tail), text)
    return (text, -1, text)


def _normalize_conditions(raw: list[tuple[str, str | None]]) -> list[tuple[str, str]]:
    """清洗组合条件：去空白、去重复，保持字段优先级顺序，重复条件只保留一次。"""
    seen: set[tuple[str, str]] = set()
    conditions: list[tuple[str, str]] = []
    for field, word in raw:
        if field not in DIMENSION_FIELDS:
            continue
        text = (word or "").strip()
        if not text:
            continue
        key = (field, text)
        if key in seen:
            continue
        seen.add(key)
        conditions.append(key)
    return conditions


class SourceService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        code: str | None = None,
        name: str | None = None,
        protocol: str | None = None,
        owner: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        rows = list(store.rows(MODULE))
        conditions = _normalize_conditions([
            ("源端编号", keyword),  # 兼容旧版 keyword 参数，等价于按源端编号定位
            ("源端编号", code),
            ("源端名称", name),
            ("接入协议", protocol),
            ("负责人", owner),
        ])
        if conditions:
            rows = [row for row in rows if self._match_any(row, conditions)]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        # 按源端编号稳定排序：同名记录按编号排列，翻页继续加载不重复也不漏项。
        rows.sort(key=lambda row: _code_sort_key(row.get("源端编号")))
        total = len(rows)
        start = max(page - 1, 0) * size
        return {
            "items": rows[start:start + size],
            "total": total,
            "conditions": [f"{field}={word}" for field, word in conditions],
            "summary": self._summary(),
        }

    @staticmethod
    def _match_any(row: dict[str, Any], conditions: list[tuple[str, str]]) -> bool:
        """任一维度条件命中即保留；只读比较，不改写行内的协议等字段。"""
        for field, word in conditions:
            if word.lower() in str(row.get(field, "")).lower():
                return True
        return False

    @staticmethod
    def _summary() -> dict[str, int]:
        """看板汇总：基于全量采集源统计，不随筛选条件变化。"""
        rows = store.rows(MODULE)
        return {
            "采集源总数": len(rows),
            "待校验采集源": sum(1 for row in rows if row.get("status") == "待校验"),
            "已启用采集源": sum(1 for row in rows if row.get("status") == "已启用"),
        }

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        return store.find(MODULE, entry_id)

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
        missing = [field for field in REQUIRED_FIELDS if not str(values.get(field) or "").strip()]
        if missing:
            return None, missing
        rows = store.rows(MODULE)
        entry = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        entry.update({field: values.get(field) for field in REQUIRED_FIELDS})
        # 目标地址、认证方式、连接超时等连接字段随登记保留，兼容既有数据口径。
        for field in OPTIONAL_FIELDS:
            if values.get(field) is not None:
                entry[field] = values.get(field)
        entry["status"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        rows.append(entry)
        return entry, []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"采集源 {entry_id} 不存在或已归档"
        if action not in ACTION_RULES:
            return None, f"动作「{action}」不属于采集源管理可执行范围"
        target = ACTION_RULES[action]
        if target not in STATUS_ORDER:
            return None, f"目标状态「{target}」不在允许的状态序列里"
        entry["status"] = target
        entry["pending"] = target != STATUS_ORDER[-1]
        entry["abnormal"] = action in NEGATIVE_ACTIONS
        self._sync_tasks(entry)
        return entry, f"采集源已{action}"

    @staticmethod
    def _sync_tasks(entry: dict[str, Any]) -> None:
        """源端状态联动关联任务：停用即挂起待办并标记异常，启用即清除异常，
        采集任务页与待办条目随源端动作一起刷新。"""
        code = str(entry.get("源端编号") or "").strip()
        if not code:
            return
        status = entry.get("status")
        for task in store.rows("task"):
            if str(task.get("关联源端") or "").strip() != code:
                continue
            if status == "已停用":
                task["pending"] = True
                task["abnormal"] = True
            elif status == "已启用":
                task["abnormal"] = False
