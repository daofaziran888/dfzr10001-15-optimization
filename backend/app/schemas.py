"""接口出入参模型：列表分页、动作结果与各模块的明细结构。"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    size: int = 20


class ListPageResult(PageResult[dict[str, Any]]):
    """扩展分页结果：回显生效条件与模块汇总，支撑空结果说明与看板待办刷新。"""

    conditions: list[str] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)


class ActionResult(BaseModel):
    ok: bool
    message: str
    entry: dict[str, Any] | None = None


class EntryPayload(BaseModel):
    """登记或修改一条业务记录时提交的字段集合。"""

    values: dict[str, Any] = Field(default_factory=dict)
    remark: str | None = None



class SourceEntry(BaseModel):
    """采集源明细结构。"""

    field_0: str | None = None  # 源端编号
    field_1: str | None = None  # 源端名称
    field_2: str | None = None  # 接入协议
    field_3: str | None = None  # 目标地址
    field_4: str | None = None  # 认证方式
    field_5: str | None = None  # 字符编码
    field_6: str | None = None  # 连接超时
    field_7: str | None = None  # 负责人

class WebsiteEntry(BaseModel):
    """抓取规则明细结构。"""

    field_0: str | None = None  # 规则编号
    field_1: str | None = None  # 目标站点
    field_2: str | None = None  # 列表选择器
    field_3: str | None = None  # 详情选择器
    field_4: str | None = None  # 翻页参数
    field_5: str | None = None  # 请求间隔
    field_6: str | None = None  # 字符编码
    field_7: str | None = None  # 重试上限

class TaskEntry(BaseModel):
    """采集任务明细结构。"""

    field_0: str | None = None  # 任务编号
    field_1: str | None = None  # 任务名称
    field_2: str | None = None  # 关联源端
    field_3: str | None = None  # 采集频率
    field_4: str | None = None  # 增量字段
    field_5: str | None = None  # 起始水位
    field_6: str | None = None  # 批次大小
    field_7: str | None = None  # 执行窗口

class ScheduleEntry(BaseModel):
    """调度计划明细结构。"""

    field_0: str | None = None  # 计划编号
    field_1: str | None = None  # 关联任务
    field_2: str | None = None  # 调度表达式
    field_3: str | None = None  # 优先级
    field_4: str | None = None  # 超时阈值
    field_5: str | None = None  # 失败策略
    field_6: str | None = None  # 通知渠道
    field_7: str | None = None  # 是否启用

class IncrementEntry(BaseModel):
    """增量游标明细结构。"""

    field_0: str | None = None  # 游标编号
    field_1: str | None = None  # 来源标识
    field_2: str | None = None  # 增量字段
    field_3: str | None = None  # 当前水位
    field_4: str | None = None  # 上次水位
    field_5: str | None = None  # 增量条数
    field_6: str | None = None  # 采集时间
    field_7: str | None = None  # 是否完成

class RpaEntry(BaseModel):
    """RPA流程明细结构。"""

    field_0: str | None = None  # 流程编号
    field_1: str | None = None  # 流程名称
    field_2: str | None = None  # 输入来源
    field_3: str | None = None  # 动作序列
    field_4: str | None = None  # 等待条件
    field_5: str | None = None  # 超时秒数
    field_6: str | None = None  # 结果字段
    field_7: str | None = None  # 运行环境

class LogEntry(BaseModel):
    """执行日志明细结构。"""

    field_0: str | None = None  # 日志编号
    field_1: str | None = None  # 关联任务
    field_2: str | None = None  # 开始时间
    field_3: str | None = None  # 结束时间
    field_4: str | None = None  # 采集行数
    field_5: str | None = None  # 成功条数
    field_6: str | None = None  # 失败条数
    field_7: str | None = None  # 错误信息

class RetryEntry(BaseModel):
    """重试策略明细结构。"""

    field_0: str | None = None  # 策略编号
    field_1: str | None = None  # 适用任务
    field_2: str | None = None  # 最大重试
    field_3: str | None = None  # 重试间隔
    field_4: str | None = None  # 退避系数
    field_5: str | None = None  # 可重试异常
    field_6: str | None = None  # 排除异常
    field_7: str | None = None  # 最终动作

class ProxyEntry(BaseModel):
    """代理配置明细结构。"""

    field_0: str | None = None  # 代理编号
    field_1: str | None = None  # 代理地址
    field_2: str | None = None  # 代理端口
    field_3: str | None = None  # 协议类型
    field_4: str | None = None  # 认证凭据
    field_5: str | None = None  # 并发上限
    field_6: str | None = None  # 冷却时间
    field_7: str | None = None  # 是否可用

class ParserEntry(BaseModel):
    """解析模板明细结构。"""

    field_0: str | None = None  # 模板编号
    field_1: str | None = None  # 输入格式
    field_2: str | None = None  # 字段映射
    field_3: str | None = None  # 类型转换
    field_4: str | None = None  # 默认值
    field_5: str | None = None  # 校验正则
    field_6: str | None = None  # 输出格式
    field_7: str | None = None  # 模板版本

class DedupEntry(BaseModel):
    """去重规则明细结构。"""

    field_0: str | None = None  # 规则编号
    field_1: str | None = None  # 目标字段
    field_2: str | None = None  # 去重粒度
    field_3: str | None = None  # 时间窗口
    field_4: str | None = None  # 去重策略
    field_5: str | None = None  # 保留规则
    field_6: str | None = None  # 落地方式
    field_7: str | None = None  # 是否启用

class ReleaseEntry(BaseModel):
    """采集版本明细结构。"""

    field_0: str | None = None  # 版本编号
    field_1: str | None = None  # 关联源端
    field_2: str | None = None  # 版本号
    field_3: str | None = None  # 变更说明
    field_4: str | None = None  # 发布人
    field_5: str | None = None  # 发布时间
    field_6: str | None = None  # 回滚版本
    field_7: str | None = None  # 是否生效

class AlertEntry(BaseModel):
    """告警规则明细结构。"""

    field_0: str | None = None  # 告警编号
    field_1: str | None = None  # 监控目标
    field_2: str | None = None  # 告警条件
    field_3: str | None = None  # 告警级别
    field_4: str | None = None  # 通知渠道
    field_5: str | None = None  # 静默时段
    field_6: str | None = None  # 聚合窗口
    field_7: str | None = None  # 是否启用

class DashboardEntry(BaseModel):
    """看板指标明细结构。"""

    field_0: str | None = None  # 指标编号
    field_1: str | None = None  # 指标名称
    field_2: str | None = None  # 统计维度
    field_3: str | None = None  # 计算公式
    field_4: str | None = None  # 刷新频率
    field_5: str | None = None  # 展示类型
    field_6: str | None = None  # 数据源
    field_7: str | None = None  # 是否展示

class StorageEntry(BaseModel):
    """存储配置明细结构。"""

    field_0: str | None = None  # 存储编号
    field_1: str | None = None  # 存储类型
    field_2: str | None = None  # 连接串
    field_3: str | None = None  # 压缩方式
    field_4: str | None = None  # 分区策略
    field_5: str | None = None  # 保留天数
    field_6: str | None = None  # 备份策略
    field_7: str | None = None  # 是否启用

class AuditEntry(BaseModel):
    """审计记录明细结构。"""

    field_0: str | None = None  # 审计编号
    field_1: str | None = None  # 操作类型
    field_2: str | None = None  # 操作对象
    field_3: str | None = None  # 操作人
    field_4: str | None = None  # 操作时间
    field_5: str | None = None  # 变更前
    field_6: str | None = None  # 变更后
    field_7: str | None = None  # 审计备注
