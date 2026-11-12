"""采集源管理接口：维护采集源，覆盖提交校验、启用配置、停用配置等动作。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas import ActionResult, EntryPayload, ListPageResult
from app.services.source import SourceService

router = APIRouter(prefix="/api/source", tags=["采集源管理"])

service = SourceService()

LIST_FIELDS = ["源端编号", "源端名称", "接入协议", "目标地址", "认证方式", "字符编码", "连接超时", "负责人"]
STATUSES = ["草稿", "待校验", "已启用", "已停用"]


@router.get("", response_model=ListPageResult)
def list_entries(
    keyword: str | None = Query(default=None, description="按源端编号检索（兼容旧参数）"),
    status: str | None = Query(default=None, description="草稿、待校验、已启用、已停用"),
    code: str | None = Query(default=None, alias="源端编号", description="按源端编号定位"),
    name: str | None = Query(default=None, alias="源端名称", description="按源端名称定位"),
    protocol: str | None = Query(default=None, alias="接入协议", description="按接入协议定位"),
    owner: str | None = Query(default=None, alias="负责人", description="按负责人定位"),
    page: int = 1,
    size: int = 20,
) -> ListPageResult:
    """按编号、名称、协议、负责人组合定位采集源：条件取并集、状态单独过滤；
    空结果回显当前条件，不报错也不清空条件。"""
    if size > 200:
        raise HTTPException(status_code=400, detail="每页最多 200 条，请缩小分页范围")
    result = service.list_entries(
        keyword=keyword,
        status=status,
        code=code,
        name=name,
        protocol=protocol,
        owner=owner,
        page=page,
        size=size,
    )
    return ListPageResult(
        items=result["items"],
        total=result["total"],
        page=page,
        size=size,
        conditions=result["conditions"],
        summary=result["summary"],
    )


@router.get("/export")
def export_entries() -> dict[str, Any]:
    """导出采集源管理清单：返回当前过滤条件下的全量数据。"""
    result = service.list_entries(page=1, size=10000)
    return {"module": "source", "total": result["total"], "items": result["items"]}


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条采集源明细；不存在时给出可读的错误说明。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"采集源 {entry_id} 不存在或已归档")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(payload: EntryPayload) -> ActionResult:
    """登记一条采集源，缺字段时说明原因而不是静默丢弃。"""
    entry, missing = service.create_entry(payload.values)
    if missing:
        return ActionResult(ok=False, message=f"缺少必填字段：{'、'.join(missing)}")
    return ActionResult(ok=True, message="采集源已登记", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
    """对单条采集源执行提交校验、启用配置、停用配置；不允许的动作会被拦下并说明原因。"""
    action = str(payload.values.get("action") or "").strip()
    entry, message = service.run_action(entry_id, action)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)
