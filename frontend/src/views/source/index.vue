<template>
  <section class="page" data-module="source">
    <header class="page-head">
      <div>
        <h2>采集源管理管理</h2>
        <p class="page-desc">维护采集源的接入配置、连接参数与状态记录，为数据采集提供可控的入口管理。</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记采集源</button>
        <button class="btn" type="button" @click="exportRows">导出采集源管理清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label v-for="field in filterFields" :key="field" class="filter-item">
        <span>{{ field }}</span>
        <input v-model="filters[field]" :placeholder="`按${field}检索`" />
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <p v-if="appliedConditions.length" class="condition-echo">
      当前条件：{{ appliedConditions.join('、') }}（任一条件命中即返回）
    </p>

    <aside v-if="detail" class="detail-panel" data-testid="source-detail">
      <header class="detail-head">
        <h3>采集源详情：{{ detail['源端编号'] ?? detail.id }}</h3>
        <button class="btn ghost" type="button" @click="closeDetail">返回列表</button>
      </header>
      <dl class="detail-grid">
        <template v-for="column in columns" :key="column">
          <dt>{{ column }}</dt>
          <dd>{{ detail[column] ?? '—' }}</dd>
        </template>
        <dt>状态</dt>
        <dd>{{ detail.status ?? '—' }}</dd>
      </dl>
    </aside>
    <p v-if="detailError" class="error-text">{{ detailError }}</p>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in columns" :key="column">{{ row[column] ?? '—' }}</td>
          <td class="row-actions">
            <button class="link" type="button" @click="openDetail(row)">详情</button>
            <button
              v-for="action in actions"
              :key="action"
              class="link"
              type="button"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + 1" class="empty-state">
            <template v-if="appliedConditions.length">
              未命中任何采集源；当前条件：{{ appliedConditions.join('、') }}。条件已保留在输入框，可调整后重新查询。
            </template>
            <template v-else>暂无采集源管理数据，可先登记采集源</template>
          </td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条采集源管理记录，已加载 {{ rows.length }} 条</span>
      <button
        v-if="rows.length < total"
        class="btn load-more"
        type="button"
        @click="loadMore"
      >
        加载更多
      </button>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { request } from '@/api/client'

type Row = Record<string, string | number | null>

type ListPayload = {
  items?: Row[]
  total?: number
  conditions?: string[]
  summary?: Record<string, number>
}

const ENDPOINT = '/api/source'
const PAGE_SIZE = 20
const columns = ["源端编号", "源端名称", "接入协议", "目标地址", "认证方式", "字符编码", "连接超时", "负责人"]
const actions = ["提交校验", "启用配置", "停用配置"]
// 多维定位条件框：编号、名称、协议、负责人可任意组合，任一命中即返回
const filterFields = ["源端编号", "源端名称", "接入协议", "负责人"]

const rows = ref<Row[]>([])
const total = ref(0)
const page = ref(1)
const errorMessage = ref('')
const appliedConditions = ref<string[]>([])
const filters = ref<Record<string, string>>({})
const stats = ref([
  { label: '采集源总数', value: 0 },
  { label: '待校验采集源', value: 0 },
  { label: '已启用采集源', value: 0 },
])
const detail = ref<Row | null>(null)
const detailError = ref('')

// 并发相同条件只发一次请求、只保留一次结果；不同条件只认最新一次响应
const inflight = new Map<string, Promise<ListPayload>>()
let latestQuery = ''

function buildQuery(targetPage: number): string {
  const params = new URLSearchParams()
  for (const field of filterFields) {
    const word = (filters.value[field] ?? '').trim()
    if (word) {
      params.set(field, word)
    }
  }
  params.set('page', String(targetPage))
  params.set('size', String(PAGE_SIZE))
  return params.toString()
}

async function fetchPage(query: string): Promise<ListPayload> {
  const pending = inflight.get(query)
  if (pending) {
    return pending
  }
  const promise = (async () => {
    const response = await request(`${ENDPOINT}?${query}`)
    if (!response.ok) {
      throw new Error('采集源列表读取失败')
    }
    return (await response.json()) as ListPayload
  })()
  inflight.set(query, promise)
  try {
    return await promise
  } finally {
    inflight.delete(query)
  }
}

function applyPayload(payload: ListPayload, targetPage: number) {
  const incoming = payload.items ?? []
  if (targetPage === 1) {
    rows.value = incoming
  } else {
    // 继续加载按 id 去重，保证后续记录不重复也不漏项
    const seen = new Set(rows.value.map((row) => String(row.id)))
    rows.value = [...rows.value, ...incoming.filter((row) => !seen.has(String(row.id)))]
  }
  total.value = payload.total ?? rows.value.length
  page.value = targetPage
  appliedConditions.value = payload.conditions ?? []
  const summary = payload.summary ?? {}
  stats.value = stats.value.map((item) => ({ ...item, value: summary[item.label] ?? item.value }))
}

async function reload() {
  errorMessage.value = ''
  const query = buildQuery(1)
  latestQuery = query
  try {
    const payload = await fetchPage(query)
    if (query !== latestQuery) {
      return
    }
    applyPayload(payload, 1)
  } catch (error) {
    if (query !== latestQuery) {
      return
    }
    errorMessage.value = error instanceof Error ? error.message : '采集源管理列表读取失败'
  }
}

async function loadMore() {
  if (rows.value.length >= total.value) {
    return
  }
  errorMessage.value = ''
  const targetPage = page.value + 1
  const query = buildQuery(targetPage)
  latestQuery = query
  try {
    const payload = await fetchPage(query)
    if (query !== latestQuery) {
      return
    }
    applyPayload(payload, targetPage)
  } catch (error) {
    if (query !== latestQuery) {
      return
    }
    errorMessage.value = error instanceof Error ? error.message : '采集源管理列表读取失败'
  }
}

function resetFilters() {
  filters.value = {}
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  errorMessage.value = '采集源登记入口尚未接入审批流'
}

async function openDetail(row: Row) {
  // 详情在页内展开，列表与条件保持原样，返回后源端编号仍在同一行
  detailError.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}`)
    if (!response.ok) {
      throw new Error(`采集源 ${row['源端编号'] ?? row.id} 详情读取失败`)
    }
    detail.value = (await response.json()) as Row
  } catch (error) {
    detailError.value = error instanceof Error ? error.message : '采集源详情读取失败'
  }
}

function closeDetail() {
  detail.value = null
}

async function runAction(action: string, row: Row) {
  errorMessage.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    })
    if (!response.ok) {
      throw new Error('采集源管理动作未生效，请稍后重试')
    }
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '采集源管理操作失败'
  }
}

onMounted(reload)
</script>
