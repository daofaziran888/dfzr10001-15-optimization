"""采集任务业务规则：状态流转、字段校验与筛选口径都收在这里。"""
from __future__ import annotations

from typing import Any

from app.store import store

MODULE = "task"
REQUIRED_FIELDS = ["任务编号", "任务名称", "关联源端"]
STATUS_ORDER = ["草稿", "待执行", "执行中", "已完成"]
ACTION_RULES = {"提交执行": "待执行", "暂停任务": "执行中", "恢复任务": "已完成"}
NEGATIVE_ACTIONS = []


class TaskService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        rows = store.rows(MODULE)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("任务编号", ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        items = [self.with_source(row) for row in rows[start:start + size]]
        return {
            "items": items,
            "total": total,
            "conditions": [f"任务编号={keyword}"] if keyword else [],
            "summary": self._summary(),
        }

    @staticmethod
    def with_source(row: dict[str, Any]) -> dict[str, Any]:
        """按源端编号解析关联源端：命中采集源时带出名称与状态，未登记时明确标注，
        避免任务页显示与源端对不上的关联信息。"""
        enriched = dict(row)
        code = str(row.get("关联源端") or "").strip()
        source = next(
            (item for item in store.rows("source") if str(item.get("源端编号") or "").strip() == code),
            None,
        )
        if source is not None:
            enriched["关联源端名称"] = source.get("源端名称")
            enriched["源端状态"] = source.get("status")
        else:
            enriched["关联源端名称"] = "未登记"
            enriched["源端状态"] = "未登记"
        return enriched

    @staticmethod
    def _summary() -> dict[str, int]:
        """看板汇总：基于全量采集任务统计，待办条目随源端动作联动后在这里体现。"""
        rows = store.rows(MODULE)
        return {
            "采集任务总数": len(rows),
            "待执行任务": sum(1 for row in rows if row.get("status") == "待执行"),
            "执行中任务": sum(1 for row in rows if row.get("status") == "执行中"),
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
        entry["status"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        rows.append(entry)
        return entry, []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"采集任务 {entry_id} 不存在或已归档"
        if action not in ACTION_RULES:
            return None, f"动作「{action}」不属于采集任务可执行范围"
        target = ACTION_RULES[action]
        if target not in STATUS_ORDER:
            return None, f"目标状态「{target}」不在允许的状态序列里"
        entry["status"] = target
        entry["pending"] = target != STATUS_ORDER[-1]
        entry["abnormal"] = action in NEGATIVE_ACTIONS
        return entry, f"采集任务已{action}"
