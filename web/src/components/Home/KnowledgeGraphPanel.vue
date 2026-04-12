<template>
  <div class="kg-panel">
    <div class="kg-toolbar">
      <div class="kg-tabs">
        <button class="kg-tab" :class="{ active: activeView === '2d' }" @click="activeView = '2d'">二维知识图谱</button>
        <button class="kg-tab kg-tab-disabled" title="即将推出">三维知识图谱球</button>
        <button class="kg-tab" :class="{ active: activeView === 'text' }" @click="activeView = 'text'">矩形文本</button>
      </div>
      <div class="kg-actions">
        <div class="kg-meta">
          <span>节点 {{ graphNodes.length }}/{{ safeNodes.length }}</span>
          <span>关系 {{ graphLinks.length }}/{{ safeLinks.length }}</span>
          <span v-if="collapsedClusterCount">收拢 {{ collapsedClusterCount }}</span>
          <span>缩放 {{ graphZoom.toFixed(2) }}</span>
        </div>
        <button class="kg-json-toggle" @click="showJson = !showJson">{{ showJson ? '隐藏 JSON' : '显示 JSON' }}</button>
      </div>
    </div>

    <div class="kg-content" :class="{ 'json-open': showJson }">
      <div class="kg-main">
        <div v-show="activeView === '2d'" class="graph-2d-wrapper">
          <div ref="graph2DRef" class="graph-2d" @click.self="clearHighlight"></div>
          <div class="kg-ops-panel">
            <input
              v-model="searchQuery"
              class="kg-search"
              placeholder="搜索节点…"
              @input="onSearch"
            />
            <div class="kg-depth-filter">
              <div class="kg-depth-label">深度筛选</div>
              <div class="kg-depth-buttons">
                <button
                  v-for="d in depthRange"
                  :key="d"
                  class="kg-depth-btn"
                  :class="{ active: filterDepth === d }"
                  :style="{ borderColor: depthColor(d), color: filterDepth === d ? '#fff' : depthColor(d), background: filterDepth === d ? depthColor(d) : 'transparent' }"
                  @click="toggleDepthFilter(d)"
                >{{ d }}</button>
              </div>
            </div>
            <div v-if="clusterMetaMap.size" class="kg-cluster-tip">
              <div class="kg-depth-label">自适应簇</div>
              <div class="kg-cluster-copy">同级子节点过多的父节点会默认收拢，点击该节点可局部展开。</div>
            </div>
          </div>
        </div>
        <div v-show="activeView === 'text'" class="graph-text">
          <div v-if="treeRoots.length" class="tree-list">
            <details v-for="n1 in treeRoots" :key="n1.id" class="tree-node depth-1" :style="{ borderLeftColor: depthColor(1) }">
              <summary class="tree-summary">{{ n1.label }}</summary>
              <div v-if="treeChildren(n1.id).length" class="tree-children">
                <details v-for="n2 in treeChildren(n1.id)" :key="n2.id" class="tree-node depth-2" :style="{ borderLeftColor: depthColor(2) }">
                  <summary class="tree-summary">{{ n2.label }}</summary>
                  <div v-if="treeChildren(n2.id).length" class="tree-children">
                    <div v-for="n3 in treeChildren(n2.id)" :key="n3.id" class="tree-node depth-3" :style="{ borderLeftColor: depthColor(3) }">
                      {{ n3.label }}
                    </div>
                  </div>
                </details>
              </div>
            </details>
          </div>
          <div v-else class="tree-empty" v-html="highlightedText"></div>
        </div>
      </div>

      <aside v-if="showJson" class="kg-json">
        <div class="kg-json-title">动态 JSON</div>
        <pre>{{ prettyDynamicPayload }}</pre>
      </aside>
    </div>

    <div class="kg-legend" v-if="nodeTypes.length">
      <span v-for="type in nodeTypes" :key="type" class="legend-item">
        <i class="legend-dot" :style="{ background: typeColor(type, isDark()) }"></i>
        {{ type }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import * as echarts from 'echarts/core';
import { GraphChart } from 'echarts/charts';
import { TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

echarts.use([GraphChart, TooltipComponent, CanvasRenderer]);

const props = defineProps({
  content: { type: String, default: '' },
  nodes: { type: Array, default: () => [] },
  links: { type: Array, default: () => [] },
  dynamicPayload: { type: Object, default: () => ({}) },
  visualConfig: { type: Object, default: () => ({}) },
});

const activeView = ref('2d');
const showJson = ref(false);
const activeNodeId = ref(null);
const highlightedNodeId = ref(null);
const pendingClusterFocusId = ref(null);
const graph2DRef = ref(null);
const graph3DRef = ref(null);
const graphZoom = ref(1);
const searchQuery = ref('');
const filterDepth = ref(null);

let chart2D = null;
let themeObserver = null;
let resizeObserver = null;
let animationFrame = null;
let clusterFollowFrame = null;
let isSyncingOverlayRoam = false;

const DEPTH_COLORS = ['#e74c3c','#f1c40f','#2ecc71','#3498db','#9b59b6','#e67e22','#1abc9c'];
const CLUSTER_CHILD_THRESHOLD = 30;
const CLUSTER_MIN_DOMINANT_TYPE_RATIO = 0.68;
const CLUSTER_MIN_LEAF_RATIO = 0.62;
const CLUSTER_MAX_AVG_LABEL = 18;
const MAIN_GRAPH_SERIES_ID = 'kg_main_graph';
const CLUSTER_OVERLAY_SERIES_ID = 'kg_cluster_overlay';
const GRAPH_DEFAULT_CENTER = ['50%', '50%'];
const depthColor = (d) => DEPTH_COLORS[d % DEPTH_COLORS.length];

const isDark = () => document.documentElement.getAttribute('data-theme') === 'dark';
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const shorten = (value, maxLen = 64) => {
  const text = String(value ?? '').replace(/\s+/g, ' ').trim();
  if (!text) return '';
  return text.length > maxLen ? `${text.slice(0, maxLen)}...` : text;
};

const isMojibakeText = (value) => {
  const text = String(value ?? '').trim();
  if (!text) return false;
  if (text.includes('&#65533;')) return true;
  const cjk = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
  const bad = (text.match(/[锟銆锛鈥鍏鏂璇缁绯绋闄勯棿鍒]/g) || []).length;
  return bad >= 3 && bad / Math.max(cjk, 1) > 0.35;
};

const sanitizeNodeLabel = (value, fallback) => {
  const text = shorten(value ?? fallback ?? '', 80);
  return isMojibakeText(text) ? '' : text;
};

const isGenericRootLabel = (text) => /^(payload|payload_root|root|root_topic|node_title|unknown|未知事项)$/i.test(String(text || '').trim());

const firstLineTitle = (text) => {
  const line = String(text || '').split(/\r?\n/).map((s) => s.trim()).find(Boolean);
  return shorten(line || '', 80);
};

const pickPayloadTitle = (payload) => {
  const visited = new Set();
  const walk = (obj, depth = 0) => {
    if (!obj || depth > 4 || visited.has(obj)) return '';
    if (typeof obj === 'string') {
      const s = shorten(obj, 80);
      return s && !isGenericRootLabel(s) ? s : '';
    }
    if (Array.isArray(obj)) {
      for (const item of obj.slice(0, 20)) { const hit = walk(item, depth + 1); if (hit) return hit; }
      return '';
    }
    if (typeof obj === 'object') {
      visited.add(obj);
      for (const [, v] of Object.entries(obj).slice(0, 40)) {
        if (typeof v === 'string') { const s = shorten(v, 80); if (s && !isGenericRootLabel(s)) return s; }
        const hit = walk(v, depth + 1);
        if (hit) return hit;
      }
    }
    return '';
  };
  return walk(payload);
};

const typeColor = (type, dark) => {
  const map = {
    主题: dark ? '#ff8b82' : '#c0392b', 对象: dark ? '#8fb2ff' : '#2f6fdd',
    流程: dark ? '#7cd1ff' : '#1f97c9', 材料: dark ? '#a9d07b' : '#4f8f2f',
    时间: dark ? '#ffd38f' : '#d18b27', 约束: dark ? '#c9a2ff' : '#8c57d1',
    风险: dark ? '#ff9cab' : '#d94f68', 实体: dark ? '#aab3c2' : '#6c7a89',
  };
  return map[type] || (dark ? '#91a5ff' : '#356fe0');
};

const baseNodes = computed(() =>
  (props.nodes || []).map((item, idx) => ({
    id: String(item?.id || `node_${idx + 1}`),
    label: sanitizeNodeLabel(item?.label, `节点${idx + 1}`),
    type: String(item?.type || '实体'),
    importance: clamp(Number(item?.importance ?? 0.5), 0, 1),
    layer: item?.layer ? String(item.layer) : '',
    group: item?.group ? String(item.group) : '',
    parent_id: item?.parent_id ? String(item.parent_id) : null,
  })).filter((item) => item.label)
);

const baseLinks = computed(() =>
  (props.links || []).map((item) => ({
    source: String(item?.source || ''),
    target: String(item?.target || ''),
    relation: (() => {
      const raw = shorten(String(item?.relation || '关联'), 20);
      return /^(展开|包含|值|关联)$/i.test(raw) ? '' : raw;
    })(),
    logic_type: String(item?.logic_type || 'positive'),
    strength: clamp(Number(item?.strength ?? 0.6), 0, 1),
  })).filter((item) => item.source && item.target)
);

const safeNodes = computed(() => baseNodes.value);

const rootNodeId = computed(() => {
  if (!safeNodes.value.length) return null;
  const focusId = String(props.visualConfig?.focus_node || '').trim();
  if (focusId) { const byFocus = safeNodes.value.find((n) => n.id === focusId); if (byFocus) return byFocus.id; }
  const sorted = [...safeNodes.value].sort((a, b) => Number(b.importance || 0) - Number(a.importance || 0));
  return sorted[0]?.id || safeNodes.value[0].id;
});

const documentTitle = computed(() => {
  const rootId = rootNodeId.value;
  const root = safeNodes.value.find((n) => n.id === rootId);
  if (root?.label && !isGenericRootLabel(root.label)) return root.label;
  const payloadTitle = pickPayloadTitle(props.dynamicPayload);
  if (payloadTitle) return payloadTitle;
  const contentTitle = firstLineTitle(props.content);
  if (contentTitle) return contentTitle;
  return '文档';
});

const safeLinks = computed(() => {
  const validIds = new Set(safeNodes.value.map((item) => item.id));
  const result = [];
  const seen = new Set();
  for (const link of baseLinks.value) {
    if (!validIds.has(link.source) || !validIds.has(link.target)) continue;
    const key = `${link.source}_${link.target}_${link.relation}`;
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(link);
  }
  return result;
});

const nodeById = computed(() => new Map(safeNodes.value.map((node) => [node.id, node])));

const graphHierarchy = computed(() => {
  if (!safeNodes.value.length || !rootNodeId.value) {
    return { parent: new Map(), depth: new Map(), children: new Map() };
  }
  return buildParentDepthMap(safeNodes.value, safeLinks.value, rootNodeId.value);
});

const collectDescendants = (nodeId, childrenMap) => {
  const result = new Set();
  const queue = [...(childrenMap.get(nodeId) || [])];
  while (queue.length) {
    const current = queue.shift();
    if (result.has(current)) continue;
    result.add(current);
    for (const child of (childrenMap.get(current) || [])) queue.push(child);
  }
  return result;
};

const clusterMetaMap = computed(() => {
  const map = new Map();
  const rootId = rootNodeId.value;
  for (const node of safeNodes.value) {
    if (!node?.id || node.id === rootId) continue;
    const children = graphHierarchy.value.children.get(node.id) || [];
    if (children.length < CLUSTER_CHILD_THRESHOLD) continue;
    const childNodes = children.map((id) => nodeById.value.get(id)).filter(Boolean);
    if (!childNodes.length) continue;
    const leafCount = childNodes.filter((child) => !(graphHierarchy.value.children.get(child.id) || []).length).length;
    const leafRatio = leafCount / childNodes.length;
    const typeCounts = new Map();
    let totalLabelLength = 0;
    for (const child of childNodes) {
      totalLabelLength += String(child.label || '').trim().length;
      const type = child.type || '实体';
      typeCounts.set(type, (typeCounts.get(type) || 0) + 1);
    }
    const dominantTypeRatio = Math.max(...typeCounts.values()) / childNodes.length;
    const avgLabelLength = totalLabelLength / childNodes.length;
    map.set(node.id, {
      childCount: childNodes.length,
      leafRatio,
      dominantTypeRatio,
      avgLabelLength,
    });
  }
  return map;
});

const userExpandedClusterIds = ref(new Set());

const autoExpandedClusterIds = computed(() => {
  const expanded = new Set();
  const query = searchQuery.value.trim().toLowerCase();
  const markAncestors = (nodeId) => {
    let current = String(nodeId || '').trim();
    const seen = new Set();
    while (current && !seen.has(current)) {
      seen.add(current);
      const parentId = graphHierarchy.value.parent.get(current);
      if (!parentId) break;
      if (clusterMetaMap.value.has(parentId)) expanded.add(parentId);
      current = parentId;
    }
  };
  if (query) {
    for (const node of safeNodes.value) {
      if (String(node.label || '').toLowerCase().includes(query)) markAncestors(node.id);
    }
  }
  if (activeNodeId.value) markAncestors(activeNodeId.value);
  if (highlightedNodeId.value) markAncestors(highlightedNodeId.value);
  return expanded;
});

const expandedClusterIds = computed(() => {
  const merged = new Set();
  for (const id of userExpandedClusterIds.value) {
    if (clusterMetaMap.value.has(id)) merged.add(id);
  }
  for (const id of autoExpandedClusterIds.value) merged.add(id);
  return merged;
});

const hiddenNodeIds = computed(() => {
  const hidden = new Set();
  for (const [clusterId] of clusterMetaMap.value.entries()) {
    if (expandedClusterIds.value.has(clusterId)) continue;
    for (const nodeId of collectDescendants(clusterId, graphHierarchy.value.children)) hidden.add(nodeId);
  }
  return hidden;
});

const graphNodes = computed(() => safeNodes.value.filter((node) => !hiddenNodeIds.value.has(node.id)));

const graphLinks = computed(() => {
  const visibleIds = new Set(graphNodes.value.map((node) => node.id));
  return safeLinks.value.filter((link) => visibleIds.has(link.source) && visibleIds.has(link.target));
});

const collapsedClusterCount = computed(() => {
  let count = 0;
  for (const [clusterId] of clusterMetaMap.value.entries()) {
    if (!expandedClusterIds.value.has(clusterId)) count += 1;
  }
  return count;
});

const expandedClusterOwnerMap = computed(() => {
  const ownerMap = new Map();
  if (!expandedClusterIds.value.size) return ownerMap;
  for (const node of graphNodes.value) {
    let current = graphHierarchy.value.parent.get(node.id);
    while (current) {
      if (expandedClusterIds.value.has(current)) {
        ownerMap.set(node.id, current);
        break;
      }
      current = graphHierarchy.value.parent.get(current);
    }
  }
  return ownerMap;
});

const expandedClusterChildNodeIds = computed(() => {
  return new Set(expandedClusterOwnerMap.value.keys());
});

const nodeTypes = computed(() => {
  const all = graphNodes.value.map((item) => item.type).filter(Boolean);
  return [...new Set(all)].slice(0, 10);
});

const textMapping = computed(() => {
  const mapping = props.visualConfig?.text_mapping;
  return mapping && typeof mapping === 'object' ? mapping : {};
});

const prettyDynamicPayload = computed(() => JSON.stringify(props.dynamicPayload || {}, null, 2));

const escapeHtml = (value) =>
  String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');

const highlightedText = computed(() => {
  const content = props.content || '';
  const ranges = Object.entries(textMapping.value).map(([nodeId, range]) => {
    if (!Array.isArray(range) || range.length < 2) return null;
    const start = Number(range[0]); const end = Number(range[1]);
    if (!Number.isFinite(start) || !Number.isFinite(end) || start < 0 || end <= start || end > content.length) return null;
    return { nodeId, start, end };
  }).filter(Boolean).sort((a, b) => a.start - b.start);
  if (!ranges.length) return escapeHtml(content);
  let cursor = 0; let html = '';
  for (const range of ranges) {
    if (range.start < cursor) continue;
    html += escapeHtml(content.slice(cursor, range.start));
    const text = escapeHtml(content.slice(range.start, range.end));
    const activeCls = range.nodeId === activeNodeId.value ? ' active' : '';
    html += `<span id="kg-anchor-${range.nodeId}" class="kg-entity${activeCls}">${text}</span>`;
    cursor = range.end;
  }
  html += escapeHtml(content.slice(cursor));
  return html;
});

// ── depth map ──────────────────────────────────────────────────────────────
const buildParentDepthMap = (nodes, links, rootId) => {
  const ids = new Set(nodes.map((n) => n.id));
  const parent = new Map();
  const children = new Map();
  parent.set(rootId, null);
  for (const node of nodes) {
    if (node.parent_id && ids.has(node.parent_id) && node.parent_id !== node.id)
      parent.set(node.id, node.parent_id);
  }
  for (const edge of links) {
    if (!ids.has(edge.source) || !ids.has(edge.target)) continue;
    if (!parent.has(edge.target) && edge.source !== edge.target)
      parent.set(edge.target, edge.source);
  }
  for (const node of nodes) { if (!parent.has(node.id)) parent.set(node.id, rootId); }
  for (const [id, p] of parent.entries()) {
    if (!p || p === id) continue;
    if (!children.has(p)) children.set(p, []);
    children.get(p).push(id);
  }
  for (const [pid, arr] of children.entries()) {
    arr.sort((a, b) => (a || '').localeCompare(b || ''));
    children.set(pid, arr);
  }
  const depth = new Map();
  const visit = (id, seen = new Set()) => {
    if (depth.has(id)) return depth.get(id);
    if (id === rootId) { depth.set(id, 0); return 0; }
    if (seen.has(id)) return 1;
    seen.add(id);
    const p = parent.get(id);
    const d = p ? visit(p, seen) + 1 : 1;
    depth.set(id, d);
    return d;
  };
  for (const node of nodes) visit(node.id);
  return { parent, depth, children };
};

// ── tree layout ────────────────────────────────────────────────────────────
const hashSeed = (text) => {
  let hash = 2166136261;
  const value = String(text || '');
  for (let i = 0; i < value.length; i++) { hash ^= value.charCodeAt(i); hash = Math.imul(hash, 16777619); }
  return Math.abs(hash >>> 0);
};

const toXY = (value, fallback = { x: 0, y: 0 }) => {
  if (Array.isArray(value)) {
    return {
      x: Number.isFinite(Number(value[0])) ? Number(value[0]) : fallback.x,
      y: Number.isFinite(Number(value[1])) ? Number(value[1]) : fallback.y,
    };
  }
  if (value && typeof value === 'object') {
    const x = value.x ?? value[0];
    const y = value.y ?? value[1];
    return {
      x: Number.isFinite(Number(x)) ? Number(x) : fallback.x,
      y: Number.isFinite(Number(y)) ? Number(y) : fallback.y,
    };
  }
  return { ...fallback };
};

const buildClusterLocalLayout = (clusterId, childrenMap, links) => {
  const subtreeIds = [...collectDescendants(clusterId, childrenMap)];
  if (!subtreeIds.length) return new Map();
  const nodeSet = new Set([clusterId, ...subtreeIds]);
  const localChildren = new Map();
  const localParent = new Map([[clusterId, null]]);
  const localDepth = new Map([[clusterId, 0]]);
  const queue = [clusterId];
  while (queue.length) {
    const current = queue.shift();
    const children = (childrenMap.get(current) || []).filter((id) => nodeSet.has(id));
    localChildren.set(current, children);
    for (const child of children) {
      if (localParent.has(child)) continue;
      localParent.set(child, current);
      localDepth.set(child, (localDepth.get(current) || 0) + 1);
      queue.push(child);
    }
  }

  const positions = new Map([[clusterId, { x: 0, y: 0 }]]);
  const velocities = new Map();
  const depthGroups = new Map();
  const orbitTargets = new Map();
  for (const id of subtreeIds) {
    const depth = localDepth.get(id) || 1;
    if (!depthGroups.has(depth)) depthGroups.set(depth, []);
    depthGroups.get(depth).push(id);
  }
  let orbitBaseRadius = 84;
  const orderedDepths = [...depthGroups.keys()].sort((a, b) => a - b);
  for (const depth of orderedDepths) {
    const ids = [...(depthGroups.get(depth) || [])].sort((a, b) => {
      const parentA = localParent.get(a) || '';
      const parentB = localParent.get(b) || '';
      return parentA.localeCompare(parentB) || a.localeCompare(b);
    });
    const orbitGap = 34 + Math.min(depth * 2, 8);
    const desiredArcGap = 32 + Math.min(depth * 3, 10);
    let cursor = 0;
    let orbitIndex = 0;
    while (cursor < ids.length) {
      const radius = orbitBaseRadius + orbitIndex * orbitGap;
      const circumference = Math.max(2 * Math.PI * radius, desiredArcGap * 6);
      const capacity = Math.max(6, Math.floor(circumference / desiredArcGap));
      const slice = ids.slice(cursor, cursor + Math.max(1, capacity));
      const orbitSeed = hashSeed(`${clusterId}_${depth}_${orbitIndex}`);
      slice.forEach((id, idx) => {
        const angle = ((Math.PI * 2 * idx) / Math.max(slice.length, 1)) + ((orbitSeed % 360) * Math.PI) / 180;
        const point = { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius };
        positions.set(id, point);
        velocities.set(id, { x: 0, y: 0 });
        orbitTargets.set(id, { radius, angle, x: point.x, y: point.y });
      });
      cursor += slice.length;
      orbitIndex += 1;
    }
    orbitBaseRadius += Math.max(orbitIndex, 1) * orbitGap + 28;
  }

  const visibleLinks = links.filter((link) => nodeSet.has(link.source) && nodeSet.has(link.target));
  const springs = visibleLinks.length
    ? visibleLinks
    : subtreeIds.map((id) => ({ source: localParent.get(id) || clusterId, target: id }));

  for (let iter = 0; iter < 90; iter++) {
    const forces = new Map(subtreeIds.map((id) => [id, { x: 0, y: 0 }]));
    for (let i = 0; i < subtreeIds.length; i++) {
      const aId = subtreeIds[i];
      const a = positions.get(aId);
      for (let j = i + 1; j < subtreeIds.length; j++) {
        const bId = subtreeIds[j];
        const b = positions.get(bId);
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const distSq = Math.max(dx * dx + dy * dy, 196);
        const dist = Math.sqrt(distSq);
        const push = 2400 / distSq;
        const fx = (dx / dist) * push;
        const fy = (dy / dist) * push;
        forces.get(aId).x += fx;
        forces.get(aId).y += fy;
        forces.get(bId).x -= fx;
        forces.get(bId).y -= fy;
      }
    }

    for (const edge of springs) {
      const source = positions.get(edge.source) || { x: 0, y: 0 };
      const target = positions.get(edge.target);
      if (!target) continue;
      const dx = source.x - target.x;
      const dy = source.y - target.y;
      const dist = Math.max(Math.hypot(dx, dy), 1);
      const sourceOrbit = orbitTargets.get(edge.source);
      const targetOrbit = orbitTargets.get(edge.target);
      const sourceRadius = sourceOrbit?.radius || 0;
      const targetRadius = targetOrbit?.radius || (localDepth.get(edge.target) || 1) * 52;
      const targetLen = Math.max(44, Math.abs(targetRadius - sourceRadius) + 22);
      const pull = (dist - targetLen) * 0.06;
      const fx = (dx / dist) * pull;
      const fy = (dy / dist) * pull;
      forces.get(edge.target).x += fx;
      forces.get(edge.target).y += fy;
    }

    for (const id of subtreeIds) {
      const point = positions.get(id);
      const force = forces.get(id);
      const orbitTarget = orbitTargets.get(id);
      const targetRadius = orbitTarget?.radius || (62 + (localDepth.get(id) || 1) * 44);
      const currentRadius = Math.max(Math.hypot(point.x, point.y), 1);
      const radialPull = (currentRadius - targetRadius) * 0.035;
      force.x -= (point.x / currentRadius) * radialPull;
      force.y -= (point.y / currentRadius) * radialPull;
      if (orbitTarget) {
        force.x += (orbitTarget.x - point.x) * 0.022;
        force.y += (orbitTarget.y - point.y) * 0.022;
      }

      const vel = velocities.get(id) || { x: 0, y: 0 };
      vel.x = (vel.x + force.x) * 0.84;
      vel.y = (vel.y + force.y) * 0.84;
      const speed = Math.hypot(vel.x, vel.y);
      if (speed > 10) {
        vel.x = (vel.x / speed) * 10;
        vel.y = (vel.y / speed) * 10;
      }
      point.x += vel.x;
      point.y += vel.y;
      velocities.set(id, vel);
    }
  }
  return positions;
};

const buildTreeLayout = (nodes, links, rootId, clusterMap = new Map(), expandedSet = new Set(), layoutHierarchy = null, clusterLayouts = new Map()) => {
  const map = new Map();
  if (!nodes.length || !rootId) return map;
  const nodeByIdLocal = new Map(nodes.map((node) => [node.id, node]));
  const { children: childrenMap } = layoutHierarchy || buildParentDepthMap(nodes, links, rootId);
  const placed = [];
  const minDist = 48;
  const placeAvoid = (x0, y0, seed) => {
    let x = x0, y = y0, r = 0, ang = ((seed % 360) * Math.PI) / 180;
    for (let k = 0; k < 80; k++) {
      if (!placed.some((p) => Math.hypot(p.x - x, p.y - y) < minDist)) break;
      r += 10; ang += 1.618; x = x0 + Math.cos(ang) * r; y = y0 + Math.sin(ang) * r;
    }
    placed.push({ x, y }); return { x, y };
  };
  map.set(rootId, { x: 0, y: 0 }); placed.push({ x: 0, y: 0 });
  const placeClusterChildren = (pid) => {
    const p = map.get(pid) || { x: 0, y: 0 };
    const localLayout = clusterLayouts.get(pid) || buildClusterLocalLayout(pid, childrenMap, links);
    for (const [nodeId, point] of localLayout.entries()) {
      if (nodeId === pid) continue;
      const pos = placeAvoid(p.x + point.x, p.y + point.y, hashSeed(`${pid}_${nodeId}`));
      map.set(nodeId, pos);
    }
  };
  const walk = (pid, depth) => {
    const children = [...(childrenMap.get(pid) || [])].sort((a, b) => {
      const aLabel = nodeByIdLocal.get(a)?.label || a;
      const bLabel = nodeByIdLocal.get(b)?.label || b;
      return aLabel.localeCompare(bLabel);
    });
    if (!children.length) return;
    const p = map.get(pid) || { x: 0, y: 0 };
    if (clusterMap.has(pid) && expandedSet.has(pid)) {
      placeClusterChildren(pid);
      return;
    }
    const n = children.length;
    const base = 136 + depth * 34;
    const offset = (hashSeed(pid) % 360) * (Math.PI / 180);
    const sector = n <= 2 ? Math.PI * 0.5 : Math.min(Math.PI * 1.8, Math.PI * 0.72 + n * 0.18);
    children.forEach((cid, idx) => {
      const clusterInfo = clusterMap.get(cid);
      const isExpandedCluster = clusterInfo && expandedSet.has(cid);
      const isCollapsedCluster = clusterInfo && !isExpandedCluster;
      const angle = n === 1 ? offset : offset - sector / 2 + (sector * idx) / Math.max(n - 1, 1);
      const extraRadius = isExpandedCluster
        ? 420 + Math.min(clusterInfo.childCount * 12, 320)
        : isCollapsedCluster
          ? 100 + Math.min(clusterInfo.childCount * 4, 120)
          : 0;
      const radius = base + extraRadius;
      const pos = placeAvoid(
        p.x + Math.cos(angle) * radius,
        p.y + Math.sin(angle) * (radius * (isExpandedCluster ? 0.88 : isCollapsedCluster ? 0.8 : 0.66)),
        hashSeed(cid),
      );
      map.set(cid, pos); walk(cid, depth + 1);
    });
  };
  walk(rootId, 1);
  return map;
};

// ── depth filter helpers ───────────────────────────────────────────────────
const depthMapCache = ref(new Map());
const expandedClusterFollowerStates = ref(new Map());

const depthRange = computed(() => {
  const depths = [...depthMapCache.value.values()];
  if (!depths.length) return [];
  const max = Math.max(...depths);
  return Array.from({ length: max + 1 }, (_, i) => i);
});

const toggleDepthFilter = (d) => {
  filterDepth.value = filterDepth.value === d ? null : d;
  applyHighlightOverlay();
};

// ── descendant helpers ─────────────────────────────────────────────────────
const getDescendants = (nodeId) => {
  const result = new Set();
  const queue = [...(graphHierarchy.value.children.get(nodeId) || [])];
  while (queue.length) {
    const cur = queue.shift();
    if (result.has(cur)) continue;
    result.add(cur);
    for (const child of (graphHierarchy.value.children.get(cur) || [])) queue.push(child);
  }
  return result;
};

const formatNodeLabel = (node) => {
  const clusterInfo = clusterMetaMap.value.get(node?.id);
  if (clusterInfo && !expandedClusterIds.value.has(node.id)) {
    return `${node.label}（${clusterInfo.childCount}）`;
  }
  return node?.label || '';
};

const toggleClusterExpansion = (nodeId) => {
  if (!clusterMetaMap.value.has(nodeId)) return false;
  const next = new Set(userExpandedClusterIds.value);
  const isExpanded = expandedClusterIds.value.has(nodeId);
  if (isExpanded) {
    next.delete(nodeId);
    const descendants = collectDescendants(nodeId, graphHierarchy.value.children);
    if (activeNodeId.value && descendants.has(activeNodeId.value)) activeNodeId.value = nodeId;
    if (highlightedNodeId.value && descendants.has(highlightedNodeId.value)) highlightedNodeId.value = nodeId;
  } else {
    next.add(nodeId);
  }
  userExpandedClusterIds.value = next;
  return true;
};

// ── 2D graph ───────────────────────────────────────────────────────────────
const shouldShowNodeLabel = (node) => {
  if (!node) return false;
  if (node.id === rootNodeId.value) return true;
  const imp = Number(node.importance || 0.5);
  const z = Number(graphZoom.value || 1);
  if (z <= 0.45) return imp >= 0.9;
  if (z <= 0.75) return imp >= 0.75;
  if (z <= 1.05) return imp >= 0.58;
  return true;
};

const shouldShowEdgeLabel = (link) => {
  const z = Number(graphZoom.value || 1);
  return z > 1.05 && Number(link?.strength || 0) >= 0.55;
};

const buildClusterAnchorId = (clusterId) => `cluster_anchor__${clusterId}`;

const getSeriesIndex = (seriesRef = MAIN_GRAPH_SERIES_ID) => {
  if (!chart2D) return -1;
  if (typeof seriesRef === 'number') return seriesRef;
  const option = chart2D.getOption?.();
  const seriesList = Array.isArray(option?.series) ? option.series : [];
  return seriesList.findIndex((series) => series?.id === seriesRef);
};

const getGraphRuntime = (seriesRef = MAIN_GRAPH_SERIES_ID) => {
  if (!chart2D) return {};
  const seriesIndex = getSeriesIndex(seriesRef);
  if (seriesIndex < 0) return {};
  const ecModel = chart2D.getModel?.();
  const seriesModel = ecModel?.getSeriesByIndex?.(seriesIndex);
  const graph = seriesModel?.getGraph?.();
  const view = seriesModel ? chart2D.getViewOfSeriesModel?.(seriesModel) : null;
  return { seriesIndex, seriesModel, graph, view };
};

const readLiveNodePositions = (seriesRef = MAIN_GRAPH_SERIES_ID) => {
  const positions = new Map();
  const { graph } = getGraphRuntime(seriesRef);
  graph?.eachNode?.((node) => {
    positions.set(node.id, toXY(node.getLayout()));
  });
  return positions;
};

const resolveEdgeCurveness = (points, edge) => {
  const explicit = Number(edge?.getModel?.()?.get?.(['lineStyle', 'curveness']) ?? 0);
  if (explicit) return explicit;
  if (!Array.isArray(points) || !points[2]) return 0;
  const p1 = toXY(points[0]);
  const p2 = toXY(points[1]);
  const c = toXY(points[2]);
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  const denom = dx * dx + dy * dy;
  if (denom < 1) return 0;
  const midX = (p1.x + p2.x) / 2;
  const midY = (p1.y + p2.y) / 2;
  return (((c.x - midX) * dy) - ((c.y - midY) * dx)) / denom;
};

const updateEdgeLayoutForPoints = (edge, sourcePoint, targetPoint) => {
  if (!edge) return false;
  const currentLayout = edge.getLayout?.();
  const currentSource = toXY(currentLayout?.[0], sourcePoint);
  const currentTarget = toXY(currentLayout?.[1], targetPoint);
  const points = Array.isArray(currentLayout) ? currentLayout.slice() : [];
  const curveness = resolveEdgeCurveness(currentLayout, edge);
  points[0] = [sourcePoint.x, sourcePoint.y];
  points[1] = [targetPoint.x, targetPoint.y];
  let changed = Math.hypot(currentSource.x - sourcePoint.x, currentSource.y - sourcePoint.y) > 0.35
    || Math.hypot(currentTarget.x - targetPoint.x, currentTarget.y - targetPoint.y) > 0.35;
  if (curveness) {
    const controlPoint = [
      (sourcePoint.x + targetPoint.x) / 2 + (targetPoint.y - sourcePoint.y) * curveness,
      (sourcePoint.y + targetPoint.y) / 2 - (targetPoint.x - sourcePoint.x) * curveness,
    ];
    const currentControl = toXY(currentLayout?.[2], { x: controlPoint[0], y: controlPoint[1] });
    if (Math.hypot(currentControl.x - controlPoint[0], currentControl.y - controlPoint[1]) > 0.35) changed = true;
    points[2] = controlPoint;
  } else if (points[2]) {
    points.length = 2;
    changed = true;
  }
  if (!changed) return false;
  edge.setLayout(points);
  return true;
};

const syncForceNodePosition = (seriesModel, graphNode, point) => {
  if (!graphNode || !point) return;
  if (seriesModel?.preservedPoints) {
    seriesModel.preservedPoints[graphNode.id] = [point.x, point.y];
  }
  if (!seriesModel?.forceLayout?.setNodePosition) return;
  seriesModel.forceLayout.setNodePosition(graphNode.dataIndex, [point.x, point.y], true);
};

const syncPreservedPointsFromLiveLayout = () => {
  const { seriesModel, graph } = getGraphRuntime(MAIN_GRAPH_SERIES_ID);
  if (!seriesModel?.preservedPoints || !graph) return;
  graph.eachNode?.((node) => {
    const point = toXY(node.getLayout());
    seriesModel.preservedPoints[node.id] = [point.x, point.y];
  });
};

const buildGraphNodeItem = (node, point, depthValue, dark, options = {}) => {
  const {
    isRoot = false,
    isCollapsedCluster = false,
    isExpandedCluster = false,
    isOverlayNode = false,
    isClusterAnchor = false,
    clusterCount = 0,
    fixed = false,
    draggable = true,
    ignoreForceRepulsion = false,
  } = options;
  if (isClusterAnchor) {
    return {
      id: node.id,
      name: '',
      value: '',
      x: point.x,
      y: point.y,
      fixed: true,
      draggable: false,
      silent: true,
      isClusterAnchor: true,
      symbolSize: 1,
      itemStyle: { color: 'rgba(0,0,0,0)', opacity: 0 },
      label: { show: false },
      tooltip: { show: false },
      emphasis: { disabled: true },
      blur: { itemStyle: { opacity: 0 } },
      select: { disabled: true },
    };
  }
  const imp = clamp(Number(node.importance || 0.5), 0, 1);
  const baseDepthSize = Math.max(10, 26 - depthValue * 2.2 + imp * 8);
  const symbolSize = isRoot
    ? 52
    : isCollapsedCluster
      ? Math.max(18, baseDepthSize + Math.min(clusterCount * 0.26, 8))
      : isExpandedCluster
        ? Math.max(isOverlayNode ? 10 : 13, baseDepthSize - (isOverlayNode ? 6 : 4))
        : isOverlayNode
          ? Math.max(7, baseDepthSize - 8)
          : baseDepthSize;
  return {
    id: node.id,
    name: isRoot ? documentTitle.value : formatNodeLabel(node),
    value: clusterCount ? `${node.type} 路 ${clusterCount} 涓瓙鑺傜偣` : node.type,
    clusterCount,
    x: point.x,
    y: point.y,
    fixed,
    ignoreForceRepulsion,
    draggable,
    isOverlayNode,
    symbolSize,
    itemStyle: {
      color: depthColor(depthValue),
      opacity: 1,
      borderWidth: isCollapsedCluster ? 2 : 0,
      borderColor: isCollapsedCluster ? (dark ? 'rgba(255,255,255,0.72)' : 'rgba(17,17,17,0.28)') : 'transparent',
      shadowBlur: isCollapsedCluster ? 14 : 0,
      shadowColor: isCollapsedCluster ? (dark ? 'rgba(255,255,255,0.18)' : 'rgba(52,73,94,0.18)') : 'transparent',
    },
    label: {
      show: shouldShowNodeLabel(node),
      color: dark ? '#f2f2f2' : '#333',
      fontSize: isRoot ? 13 : isOverlayNode ? 10 : 11,
      fontWeight: isRoot ? 700 : 400,
      formatter: () => shorten(isRoot ? documentTitle.value : formatNodeLabel(node), isRoot ? 38 : isOverlayNode ? 18 : 24),
    },
  };
};

const buildEdgeItem = (link, dark, source = link.source, target = link.target, options = {}) => {
  const {
    ignoreForceLayout = false,
    widthScale = 1,
    opacity = 0.85,
  } = options;
  return {
    source,
    target,
    value: link.relation,
    ignoreForceLayout,
    lineStyle: {
      color: link.logic_type === 'negative' ? '#e74c3c' : dark ? '#9da5b3' : '#7f8c8d',
      type: link.logic_type === 'negative' ? 'dashed' : 'solid',
      width: (0.7 + clamp(Number(link.strength || 0.6), 0, 1) * 2.2) * widthScale,
      opacity,
    },
    label: {
      show: shouldShowEdgeLabel(link),
      formatter: () => shorten(link.relation, 10),
      color: dark ? '#d6d6d6' : '#666',
      fontSize: 10,
    },
  };
};

const syncExpandedClusterFollowers = () => {
  if (!chart2D || activeView.value !== '2d' || !expandedClusterFollowerStates.value.size) return;
  const mainRuntime = getGraphRuntime(MAIN_GRAPH_SERIES_ID);
  const overlayRuntime = getGraphRuntime(CLUSTER_OVERLAY_SERIES_ID);
  if (!mainRuntime.seriesModel || !mainRuntime.graph || !mainRuntime.view || !overlayRuntime.seriesModel || !overlayRuntime.graph || !overlayRuntime.view) return;
  const option = chart2D.getOption?.();
  const seriesList = Array.isArray(option?.series) ? option.series : [];
  const mainSeries = seriesList.find((series) => series?.id === MAIN_GRAPH_SERIES_ID);
  const overlaySeries = seriesList.find((series) => series?.id === CLUSTER_OVERLAY_SERIES_ID);
  if (mainSeries && overlaySeries) {
    const mainCenter = Array.isArray(mainSeries.center) ? mainSeries.center : GRAPH_DEFAULT_CENTER;
    const overlayCenter = Array.isArray(overlaySeries.center) ? overlaySeries.center : GRAPH_DEFAULT_CENTER;
    const mainZoom = clamp(Number(mainSeries.zoom || graphZoom.value || 1), 0.2, 2.8);
    const overlayZoom = clamp(Number(overlaySeries.zoom || graphZoom.value || 1), 0.2, 2.8);
    if (mainCenter[0] !== overlayCenter[0] || mainCenter[1] !== overlayCenter[1] || Math.abs(mainZoom - overlayZoom) > 0.0001) {
      chart2D.setOption({
        series: [{
          id: CLUSTER_OVERLAY_SERIES_ID,
          center: [...mainCenter],
          zoom: mainZoom,
        }],
      });
    }
  }
  let overlayUpdated = false;
  for (const [clusterId, state] of expandedClusterFollowerStates.value.entries()) {
    const rootNode = mainRuntime.graph.getNodeById(clusterId);
    if (!rootNode) continue;
    const liveRootPoint = toXY(rootNode.getLayout());
    const lastDisplayRootPoint = toXY(state.displayRootPoint, liveRootPoint);
    const rootDeltaX = liveRootPoint.x - lastDisplayRootPoint.x;
    const rootDeltaY = liveRootPoint.y - lastDisplayRootPoint.y;
    const rootDelta = Math.hypot(rootDeltaX, rootDeltaY);
    const rootPoint = rootDelta <= 0.8
      ? lastDisplayRootPoint
      : {
          x: lastDisplayRootPoint.x + rootDeltaX * (rootDelta > 36 ? 0.34 : 0.18),
          y: lastDisplayRootPoint.y + rootDeltaY * (rootDelta > 36 ? 0.34 : 0.18),
        };
    state.displayRootPoint = rootPoint;
    const anchorNode = overlayRuntime.graph.getNodeById(state.anchorId);
    if (anchorNode) {
      const currentAnchor = toXY(anchorNode.getLayout(), rootPoint);
      if (Math.hypot(currentAnchor.x - rootPoint.x, currentAnchor.y - rootPoint.y) > 0.6) {
        anchorNode.setLayout([rootPoint.x, rootPoint.y]);
        overlayUpdated = true;
      }
    }
    for (const [nodeId, offset] of state.offsets.entries()) {
      const node = overlayRuntime.graph.getNodeById(nodeId);
      if (!node) continue;
      const target = { x: rootPoint.x + offset.x, y: rootPoint.y + offset.y };
      const current = toXY(node.getLayout(), target);
      if (Math.hypot(current.x - target.x, current.y - target.y) > 0.6) {
        node.setLayout([target.x, target.y]);
        overlayUpdated = true;
      }
    }
    for (const edgeRef of state.edges) {
      const sourceNode = overlayRuntime.graph.getNodeById(edgeRef.source);
      const targetNode = overlayRuntime.graph.getNodeById(edgeRef.target);
      if (!sourceNode || !targetNode) continue;
      const edge = overlayRuntime.graph.getEdge(edgeRef.source, edgeRef.target) || overlayRuntime.graph.getEdge(edgeRef.target, edgeRef.source);
      overlayUpdated = updateEdgeLayoutForPoints(
        edge,
        toXY(sourceNode.getLayout()),
        toXY(targetNode.getLayout()),
      ) || overlayUpdated;
    }
  }
  if (overlayUpdated) overlayRuntime.view.updateLayout(overlayRuntime.seriesModel);
};

const stopClusterFollowerSync = () => {
  if (!clusterFollowFrame) return;
  cancelAnimationFrame(clusterFollowFrame);
  clusterFollowFrame = null;
};

const startClusterFollowerSync = () => {
  stopClusterFollowerSync();
  if (activeView.value !== '2d' || !expandedClusterFollowerStates.value.size) return;
  syncPreservedPointsFromLiveLayout();
  const tick = () => {
    clusterFollowFrame = requestAnimationFrame(tick);
    syncExpandedClusterFollowers();
  };
  tick();
};

const focusClusterInView = (clusterId) => {
  if (!chart2D || !graph2DRef.value || !clusterId) return;
  const option = chart2D.getOption?.();
  const series = (Array.isArray(option?.series) ? option.series : []).find((item) => item?.id === MAIN_GRAPH_SERIES_ID);
  const data = Array.isArray(series?.data) ? series.data : [];
  const target = data.find((item) => String(item?.id || '') === String(clusterId));
  const mainSeriesIndex = getSeriesIndex(MAIN_GRAPH_SERIES_ID);
  if (!target || mainSeriesIndex < 0) return;
  let pixel = null;
  try {
    pixel = chart2D.convertToPixel({ seriesIndex: mainSeriesIndex }, [Number(target.x || 0), Number(target.y || 0)]);
  } catch {
    pixel = null;
  }
  if (!Array.isArray(pixel) || pixel.length < 2) return;
  const rect = graph2DRef.value.getBoundingClientRect();
  const desiredX = rect.width * 0.72;
  const desiredY = rect.height * 0.5;
  const dx = desiredX - pixel[0];
  const dy = desiredY - pixel[1];
  if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
    chart2D.dispatchAction({ type: 'graphRoam', seriesIndex: mainSeriesIndex, dx, dy });
  }
  const zoomFactor = 0.82;
  const nextZoom = clamp(graphZoom.value * zoomFactor, 0.2, 2.8);
  if (nextZoom < graphZoom.value - 0.02) {
    chart2D.dispatchAction({ type: 'graphRoam', seriesIndex: mainSeriesIndex, zoom: zoomFactor, originX: desiredX, originY: desiredY });
    graphZoom.value = nextZoom;
  }
};

const findSeriesNodeRefsById = (nodeId) => {
  if (!chart2D || !nodeId) return [];
  const option = chart2D.getOption?.();
  const seriesList = Array.isArray(option?.series) ? option.series : [];
  const refs = [];
  seriesList.forEach((series, seriesIndex) => {
    const data = Array.isArray(series?.data) ? series.data : [];
    const dataIndex = data.findIndex((item) => String(item?.id || '') === String(nodeId));
    if (dataIndex >= 0) refs.push({ seriesIndex, dataIndex });
  });
  return refs;
};

const applySimpleNodeEmphasis = (nextId, prevId = null) => {
  if (!chart2D) return;
  const previousRefs = findSeriesNodeRefsById(prevId || highlightedNodeId.value);
  previousRefs.forEach(({ seriesIndex, dataIndex }) => {
    chart2D.dispatchAction({ type: 'downplay', seriesIndex, dataIndex });
  });
  const nextRefs = findSeriesNodeRefsById(nextId);
  nextRefs.forEach(({ seriesIndex, dataIndex }) => {
    chart2D.dispatchAction({ type: 'highlight', seriesIndex, dataIndex });
  });
};

const clearSimpleNodeEmphasis = (nodeId = highlightedNodeId.value) => {
  if (!chart2D || !nodeId) return;
  findSeriesNodeRefsById(nodeId).forEach(({ seriesIndex, dataIndex }) => {
    chart2D.dispatchAction({ type: 'downplay', seriesIndex, dataIndex });
  });
};

const syncOverlayRoam = (payload, targetSeriesRef = CLUSTER_OVERLAY_SERIES_ID) => {
  const targetSeriesIndex = getSeriesIndex(targetSeriesRef);
  if (targetSeriesIndex < 0) return;
  const sourceSeriesId = String(payload?.seriesId || '').trim();
  const sourceSeriesIndex = sourceSeriesId ? getSeriesIndex(sourceSeriesId) : Number(payload?.seriesIndex);
  const option = chart2D?.getOption?.();
  const seriesList = Array.isArray(option?.series) ? option.series : [];
  const sourceSeries = seriesList[sourceSeriesIndex];
  if (!sourceSeries) return;
  const center = Array.isArray(sourceSeries.center) ? [...sourceSeries.center] : [...GRAPH_DEFAULT_CENTER];
  const zoom = clamp(Number(sourceSeries.zoom || graphZoom.value || 1), 0.2, 2.8);
  isSyncingOverlayRoam = true;
  try {
    chart2D.setOption({
      series: [{
        id: typeof targetSeriesRef === 'number' ? seriesList[targetSeriesIndex]?.id : targetSeriesRef,
        center,
        zoom,
      }],
    });
  } finally {
    isSyncingOverlayRoam = false;
  }
};

const decorateDisplayedNode = (item, livePositions, dark) => {
  const id = String(item?.id || '');
  const point = livePositions.get(id);
  if (item?.isClusterAnchor) {
    return {
      ...item,
      x: point?.x ?? item.x,
      y: point?.y ?? item.y,
    };
  }
  const src = nodeById.value.get(id);
  const depthValue = Number(depthMapCache.value.get(id) ?? 0);
  const isRoot = id === rootNodeId.value;
  const baseCol = depthColor(depthValue);
  const clusterInfo = clusterMetaMap.value.get(id);
  const isCollapsedCluster = clusterInfo && !expandedClusterIds.value.has(id);
  const query = searchQuery.value.trim().toLowerCase();
  const matchesSearch = query && src?.label?.toLowerCase().includes(query);
  const matchesDepth = filterDepth.value !== null && depthValue === filterDepth.value;
  const descendants = highlightedNodeId.value ? getDescendants(highlightedNodeId.value) : null;

  let color = baseCol;
  let opacity = 1;
  let borderWidth = isCollapsedCluster ? 3 : 0;
  let borderColor = isCollapsedCluster ? (dark ? 'rgba(255,255,255,0.72)' : 'rgba(17,17,17,0.28)') : 'transparent';
  let labelShow = shouldShowNodeLabel(src || { id, importance: 0.5 });

  if (highlightedNodeId.value) {
    if (id === highlightedNodeId.value) {
      color = baseCol;
      borderWidth = 4;
      borderColor = '#fff';
      opacity = 1;
    } else if (descendants?.has(id)) {
      opacity = 0.85;
    } else {
      opacity = 0.15;
      labelShow = false;
    }
  } else if (matchesSearch || matchesDepth) {
    borderWidth = 3;
    borderColor = '#fff';
    opacity = 1;
  } else if (query || filterDepth.value !== null) {
    opacity = 0.2;
    labelShow = false;
  }

  return {
    ...item,
    x: point?.x ?? item.x,
    y: point?.y ?? item.y,
    name: isRoot ? documentTitle.value : formatNodeLabel(src || item),
    itemStyle: { ...(item.itemStyle || {}), color, opacity, borderWidth, borderColor },
    label: {
      ...item.label,
      show: labelShow,
      color: dark ? '#f2f2f2' : '#333',
      fontSize: isRoot ? 14 : item?.isOverlayNode ? 10 : 12,
      fontWeight: isRoot ? 700 : 400,
    },
  };
};

const applyHighlightOverlay = () => {
  if (!chart2D) return;
  syncPreservedPointsFromLiveLayout();
  const option = chart2D.getOption?.();
  const seriesList = Array.isArray(option?.series) ? option.series : [];
  if (!seriesList.length) return;
  const dark = isDark();
  const nextSeries = [];
  const mainSeries = seriesList.find((series) => series?.id === MAIN_GRAPH_SERIES_ID);
  if (mainSeries?.data) {
    const livePositions = readLiveNodePositions(MAIN_GRAPH_SERIES_ID);
    nextSeries.push({
      id: MAIN_GRAPH_SERIES_ID,
      data: mainSeries.data.map((item) => decorateDisplayedNode(item, livePositions, dark)),
    });
  }
  const overlaySeries = seriesList.find((series) => series?.id === CLUSTER_OVERLAY_SERIES_ID);
  if (overlaySeries?.data) {
    const livePositions = readLiveNodePositions(CLUSTER_OVERLAY_SERIES_ID);
    nextSeries.push({
      id: CLUSTER_OVERLAY_SERIES_ID,
      data: overlaySeries.data.map((item) => decorateDisplayedNode(item, livePositions, dark)),
    });
  }
  if (nextSeries.length) chart2D.setOption({ series: nextSeries });
};

const onSearch = () => {
  highlightedNodeId.value = null;
  filterDepth.value = null;
  nextTick(() => { render2DGraph(); });
};

const clearHighlight = () => {
  const hadSearchOrDepth = !!searchQuery.value || filterDepth.value !== null;
  clearSimpleNodeEmphasis();
  highlightedNodeId.value = null;
  searchQuery.value = '';
  filterDepth.value = null;
  if (hadSearchOrDepth) nextTick(() => { render2DGraph(); });
};

const render2DGraph = () => {
  if (!graph2DRef.value) return;
  stopClusterFollowerSync();
  if (!chart2D) chart2D = echarts.init(graph2DRef.value);
  else chart2D.clear();
  const dark = isDark();
  const rootId = rootNodeId.value;
  const hierarchy = buildParentDepthMap(graphNodes.value, graphLinks.value, rootId);
  const { depth, children } = hierarchy;
  const clusterLayouts = new Map();
  const orderedExpandedClusterIds = [...expandedClusterIds.value].sort((a, b) => {
    const depthA = Number(hierarchy.depth.get(a) ?? 0);
    const depthB = Number(hierarchy.depth.get(b) ?? 0);
    return depthA - depthB;
  });
  for (const clusterId of orderedExpandedClusterIds) {
    clusterLayouts.set(clusterId, buildClusterLocalLayout(clusterId, children, graphLinks.value));
  }
  const posMap = buildTreeLayout(
    graphNodes.value,
    graphLinks.value,
    rootId,
    clusterMetaMap.value,
    expandedClusterIds.value,
    hierarchy,
    clusterLayouts,
  );
  depthMapCache.value = depth;
  const overlayOwnedNodeIds = new Set(
    [...expandedClusterOwnerMap.value.entries()]
      .filter(([nodeId]) => !expandedClusterIds.value.has(nodeId))
      .map(([nodeId]) => nodeId),
  );
  const mainNodes = graphNodes.value.filter((node) => !overlayOwnedNodeIds.has(node.id));
  const mainNodeIds = new Set(mainNodes.map((node) => node.id));
  const mainLinks = graphLinks.value.filter((link) => mainNodeIds.has(link.source) && mainNodeIds.has(link.target));
  const graphLinkLookup = new Map();
  graphLinks.value.forEach((link) => {
    if (!graphLinkLookup.has(`${link.source}__${link.target}`)) graphLinkLookup.set(`${link.source}__${link.target}`, link);
    if (!graphLinkLookup.has(`${link.target}__${link.source}`)) graphLinkLookup.set(`${link.target}__${link.source}`, link);
  });

  const followerStates = new Map();
  const overlayNodeData = [];
  const overlayEdgeData = [];
  for (const clusterId of orderedExpandedClusterIds) {
    const layout = clusterLayouts.get(clusterId);
    if (!layout) continue;
    const childIds = [...expandedClusterOwnerMap.value.entries()]
      .filter(([nodeId, ownerId]) => ownerId === clusterId && !expandedClusterIds.value.has(nodeId))
      .map(([nodeId]) => nodeId)
      .filter((nodeId) => layout.has(nodeId));
    if (!childIds.length) continue;
    const childSet = new Set(childIds);
    const clusterPoint = posMap.get(clusterId) || { x: 0, y: 0 };
    const anchorId = buildClusterAnchorId(clusterId);
    overlayNodeData.push(buildGraphNodeItem(
      { id: anchorId, label: '', type: '', importance: 0 },
      clusterPoint,
      Number(depth.get(clusterId) ?? 0),
      dark,
      { isClusterAnchor: true },
    ));
    const offsets = new Map();
    childIds.forEach((nodeId) => {
      const node = nodeById.value.get(nodeId);
      if (!node) return;
      const offset = layout.get(nodeId) || { x: 0, y: 0 };
      offsets.set(nodeId, { ...offset });
      const point = { x: clusterPoint.x + offset.x, y: clusterPoint.y + offset.y };
      const clusterInfo = clusterMetaMap.value.get(nodeId);
      overlayNodeData.push(buildGraphNodeItem(
        node,
        point,
        Number(depth.get(nodeId) ?? 0),
        dark,
        {
          isCollapsedCluster: !!(clusterInfo && !expandedClusterIds.value.has(nodeId)),
          isExpandedCluster: !!(clusterInfo && expandedClusterIds.value.has(nodeId)),
          isOverlayNode: true,
          clusterCount: clusterInfo?.childCount || 0,
          fixed: true,
          draggable: false,
        },
      ));
    });

    const edgeKeys = new Set();
    const edgeRefs = [];
    const pushOverlayEdge = (link, sourceId, targetId) => {
      if (!sourceId || !targetId || sourceId === targetId) return;
      const key = `${sourceId}__${targetId}__${link.relation || ''}__${link.logic_type || ''}`;
      if (edgeKeys.has(key)) return;
      edgeKeys.add(key);
      overlayEdgeData.push(buildEdgeItem(link, dark, sourceId, targetId, { widthScale: 0.88, opacity: 0.78 }));
      edgeRefs.push({ source: sourceId, target: targetId });
    };

    childIds.forEach((nodeId) => {
      const parentId = hierarchy.parent.get(nodeId);
      if (!parentId || (parentId !== clusterId && !childSet.has(parentId))) return;
      const rawLink = graphLinkLookup.get(`${parentId}__${nodeId}`) || graphLinkLookup.get(`${nodeId}__${parentId}`) || {
        source: parentId,
        target: nodeId,
        relation: '',
        logic_type: 'positive',
        strength: 0.48,
      };
      pushOverlayEdge(rawLink, parentId === clusterId ? anchorId : parentId, nodeId);
    });
    graphLinks.value.forEach((link) => {
      if (!childSet.has(link.source) || !childSet.has(link.target)) return;
      pushOverlayEdge(link, link.source, link.target);
    });

    const docRootPoint = posMap.get(rootId) || { x: 0, y: 0 };
    const rootDx = clusterPoint.x - docRootPoint.x;
    const rootDy = clusterPoint.y - docRootPoint.y;
    const rootDistance = Math.hypot(rootDx, rootDy);
    const preferredDirection = rootDistance > 1
      ? { x: rootDx / rootDistance, y: rootDy / rootDistance }
      : (() => {
          const angle = ((hashSeed(`cluster_dir_${clusterId}`) % 360) * Math.PI) / 180;
          return { x: Math.cos(angle), y: Math.sin(angle) };
        })();
    followerStates.set(clusterId, {
      anchorId,
      offsets,
      edges: edgeRefs,
      displayRootPoint: { ...clusterPoint },
      minRootDistance: Math.max(rootDistance * 1.02, 760 + Math.min(childIds.length * 2.4, 140)),
      preferredDirection,
    });
  }
  expandedClusterFollowerStates.value = followerStates;

  const nodeData = mainNodes.map((node) => {
    const isRoot = node.id === rootId;
    const clusterInfo = clusterMetaMap.value.get(node.id);
    const isCollapsedCluster = clusterInfo && !expandedClusterIds.value.has(node.id);
    const isExpandedCluster = clusterInfo && expandedClusterIds.value.has(node.id);
    const isExpandedClusterChild = false;
    const imp = clamp(Number(node.importance || 0.5), 0, 1);
    const pos = posMap.get(node.id) || { x: 0, y: 0 };
    const d = Number(depth.get(node.id) ?? 0);
    const baseDepthSize = Math.max(10, 26 - d * 2.2 + imp * 8);
    const symbolSize = isRoot
      ? 52
      : isCollapsedCluster
        ? Math.max(18, baseDepthSize + Math.min(clusterInfo.childCount * 0.26, 8))
        : isExpandedCluster
          ? Math.max(13, baseDepthSize - 4)
          : isExpandedClusterChild
            ? Math.max(9, baseDepthSize - 6)
            : baseDepthSize;
    const isPinned = node.id === rootId;
    return {
      id: node.id,
      name: isRoot ? documentTitle.value : formatNodeLabel(node),
      value: clusterInfo ? `${node.type} · ${clusterInfo.childCount} 个子节点` : node.type,
      clusterCount: clusterInfo?.childCount || 0,
      x: pos.x, y: pos.y,
      fixed: isPinned,
      ignoreForceRepulsion: isExpandedClusterChild,
      symbolSize,
      draggable: node.id !== rootId,
      itemStyle: {
        color: depthColor(d),
        opacity: 1,
        borderWidth: isCollapsedCluster ? 2 : 0,
        borderColor: isCollapsedCluster ? (dark ? 'rgba(255,255,255,0.72)' : 'rgba(17,17,17,0.28)') : 'transparent',
        shadowBlur: isCollapsedCluster ? 14 : 0,
        shadowColor: isCollapsedCluster ? (dark ? 'rgba(255,255,255,0.18)' : 'rgba(52,73,94,0.18)') : 'transparent',
      },
      label: {
        show: shouldShowNodeLabel(node),
        color: dark ? '#f2f2f2' : '#333',
        fontSize: isRoot ? 13 : 11,
        fontWeight: isRoot ? 700 : 400,
        formatter: () => shorten(isRoot ? documentTitle.value : formatNodeLabel(node), isRoot ? 38 : 24),
      },
    };
  });

  const edgeData = mainLinks.map((link) => ({
    source: link.source,
    target: link.target,
    value: link.relation,
    ignoreForceLayout: false,
    lineStyle: {
      color: link.logic_type === 'negative' ? '#e74c3c' : dark ? '#9da5b3' : '#7f8c8d',
      type: link.logic_type === 'negative' ? 'dashed' : 'solid',
      width: 0.7 + clamp(Number(link.strength || 0.6), 0, 1) * 2.2,
      opacity: 0.85,
    },
    label: { show: shouldShowEdgeLabel(link), formatter: () => shorten(link.relation, 10), color: dark ? '#d6d6d6' : '#666', fontSize: 10 },
  }));
  const series = [{
    id: MAIN_GRAPH_SERIES_ID,
    type: 'graph',
    layout: 'force',
    layoutAnimation: true,
    roam: true,
    center: [...GRAPH_DEFAULT_CENTER],
    zoom: clamp(graphZoom.value || 1, 0.2, 2.8),
    data: nodeData,
    links: edgeData,
    edgeSymbol: ['none', 'arrow'],
    edgeSymbolSize: 8,
    force: {
      repulsion: [110, 240],
      gravity: 0.05,
      edgeLength: [70, 150],
      friction: 0.82,
      layoutAnimation: true,
    },
  }];
  if (overlayNodeData.length) {
    series.push({
      id: CLUSTER_OVERLAY_SERIES_ID,
      type: 'graph',
      layout: 'none',
      roam: true,
      center: [...GRAPH_DEFAULT_CENTER],
      zoom: clamp(graphZoom.value || 1, 0.2, 2.8),
      data: overlayNodeData,
      links: overlayEdgeData,
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: 6,
      animation: false,
      z: 3,
      emphasis: { focus: 'none' },
    });
  }

  chart2D.setOption({
    backgroundColor: 'transparent',
    animationDurationUpdate: 350,
    tooltip: {
      trigger: 'item',
      backgroundColor: dark ? 'rgba(20,20,20,0.95)' : 'rgba(255,255,255,0.95)',
      borderColor: dark ? '#444' : '#ddd',
      textStyle: { color: dark ? '#f2f2f2' : '#333' },
      formatter: (params) => {
        if (params.dataType === 'edge') return `${params.data.value || '关系'}`;
        const clusterLine = params.data?.clusterCount ? `<br/>默认收拢 ${params.data.clusterCount} 个子节点` : '';
        return `${params.name}<br/>${params.data.value || ''}${clusterLine}`;
      },
    },
    series,
  }, { replaceMerge: ['series'] });

  chart2D.off('click');
  chart2D.on('click', (params) => {
    if (params.dataType === 'node' && params.data?.id && !params.data?.isClusterAnchor) {
      const id = params.data.id;
      if (toggleClusterExpansion(id)) {
        highlightedNodeId.value = null;
        activeNodeId.value = id;
        searchQuery.value = '';
        filterDepth.value = null;
        pendingClusterFocusId.value = id;
        nextTick(() => { render2DGraph(); });
        return;
      }
      if (highlightedNodeId.value === id) { clearHighlight(); return; }
      const prevHighlightedId = highlightedNodeId.value;
      highlightedNodeId.value = id;
      activeNodeId.value = id;
      searchQuery.value = '';
      filterDepth.value = null;
      applySimpleNodeEmphasis(id, prevHighlightedId);
    } else if (params.dataType !== 'edge') {
      clearHighlight();
    }
  });

  chart2D.off('graphRoam');
  chart2D.on('graphRoam', (params = {}) => {
    const option = chart2D?.getOption?.();
    const seriesList = Array.isArray(option?.series) ? option.series : [];
    const mainSeriesIndex = getSeriesIndex(MAIN_GRAPH_SERIES_ID);
    const overlaySeriesIndex = getSeriesIndex(CLUSTER_OVERLAY_SERIES_ID);
    const sourceSeriesId = String(params?.seriesId || '').trim();
    const sourceIndex = sourceSeriesId ? getSeriesIndex(sourceSeriesId) : Number(params?.seriesIndex);
    const sourceSeries = seriesList[Number.isFinite(sourceIndex) ? sourceIndex : (mainSeriesIndex >= 0 ? mainSeriesIndex : 0)];
    const z = Number(sourceSeries?.zoom || seriesList[mainSeriesIndex >= 0 ? mainSeriesIndex : 0]?.zoom || 1);
    graphZoom.value = clamp(z, 0.2, 2.8);
    if (isSyncingOverlayRoam) return;
    if (!Number.isFinite(sourceIndex)) return;
    if (sourceIndex === mainSeriesIndex && overlaySeriesIndex >= 0) {
      syncOverlayRoam(params, overlaySeriesIndex);
    } else if (sourceIndex === overlaySeriesIndex && mainSeriesIndex >= 0) {
      syncOverlayRoam(params, mainSeriesIndex);
    }
  });

  applyHighlightOverlay();
  if (pendingClusterFocusId.value) {
    const focusId = pendingClusterFocusId.value;
    pendingClusterFocusId.value = null;
    nextTick(() => { focusClusterInView(focusId); });
  }
  startClusterFollowerSync();
};

// ── Three.js (kept for future use, 3D tab disabled in UI) ─────────────────
let threeRenderer = null, threeScene = null, threeCamera = null;
let threeControls = null, threeRaycaster = null, threePointer = null;
const threeNodeMeshes = new Map();
const threeEdgeRefs = [];
const threeNodeMeta = new Map();

const disposeThreeGraph = () => {
  for (const mesh of threeNodeMeshes.values()) { mesh.geometry?.dispose?.(); mesh.material?.dispose?.(); threeScene?.remove(mesh); }
  threeNodeMeshes.clear();
  for (const edge of threeEdgeRefs.splice(0, threeEdgeRefs.length)) { edge.line.geometry?.dispose?.(); edge.line.material?.dispose?.(); threeScene?.remove(edge.line); }
  threeNodeMeta.clear();
};

const ensureThreeScene = () => {
  const container = graph3DRef?.value;
  if (!container) return false;
  if (threeRenderer) return true;
  threeScene = new THREE.Scene();
  threeCamera = new THREE.PerspectiveCamera(48, 1, 0.1, 5000);
  threeCamera.position.set(0, 0, 760);
  threeRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  threeRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  threeRenderer.setClearColor(0x000000, 0);
  threeRenderer.domElement.style.cssText = 'width:100%;height:100%;display:block';
  container.innerHTML = '';
  container.appendChild(threeRenderer.domElement);
  threeControls = new OrbitControls(threeCamera, threeRenderer.domElement);
  Object.assign(threeControls, { enableDamping: true, dampingFactor: 0.07, rotateSpeed: 0.7, zoomSpeed: 0.85, enablePan: false, minDistance: 220, maxDistance: 1800 });
  threeScene.add(new THREE.AmbientLight(0xffffff, 0.85));
  const dir = new THREE.DirectionalLight(0xffffff, 0.65); dir.position.set(160, 220, 260); threeScene.add(dir);
  threeRaycaster = new THREE.Raycaster(); threePointer = new THREE.Vector2();
  threeRenderer.domElement.addEventListener('pointerdown', onThreePointerDown);
  resizeThreeRenderer(); return true;
};

const resizeThreeRenderer = () => {
  if (!threeRenderer || !threeCamera || !graph3DRef?.value) return;
  const rect = graph3DRef.value.getBoundingClientRect();
  if (!rect.width || !rect.height) return;
  threeRenderer.setSize(rect.width, rect.height, false);
  threeCamera.aspect = rect.width / rect.height;
  threeCamera.updateProjectionMatrix();
};

const pick3DNodes = () => {
  const MAX_3D = 120; const rootId = rootNodeId.value;
  const root = safeNodes.value.find((n) => n.id === rootId);
  const others = safeNodes.value.filter((n) => n.id !== rootId).sort((a, b) => Number(b.importance || 0) - Number(a.importance || 0));
  return root ? [root, ...others.slice(0, MAX_3D - 1)] : others.slice(0, MAX_3D);
};

const rebuildThreeGraph = () => {
  if (!ensureThreeScene()) return;
  disposeThreeGraph();
  const rootId = rootNodeId.value; if (!rootId) return;
  const nodes = pick3DNodes(); const idSet = new Set(nodes.map((n) => n.id));
  const links = safeLinks.value.filter((e) => idSet.has(e.source) && idSet.has(e.target));
  const posMap = buildTreeLayout(nodes, links, rootId);
  const { parent, depth } = buildParentDepthMap(nodes, links, rootId);
  const dark = isDark();
  for (const node of nodes) {
    const id = node.id; const d = Number(depth.get(id) || 0); const isRoot = id === rootId;
    const anchor2D = posMap.get(id) || { x: 0, y: 0 }; const seed = hashSeed(id);
    const parentId = parent.get(id); const parentAnchor = parentId && posMap.get(parentId) ? posMap.get(parentId) : { x: 0, y: 0 };
    const angle = ((seed % 360) * Math.PI) / 180; const ring = 36 + d * 20;
    const ax = isRoot ? 0 : parentAnchor.x * 0.7 + Math.cos(angle) * ring;
    const ay = isRoot ? 0 : parentAnchor.y * 0.7 + Math.sin(angle) * ring;
    const az = isRoot ? 0 : ((seed % 140) - 70) * 0.85 + d * 24;
    const anchor = new THREE.Vector3(ax || anchor2D.x * 0.6, ay || anchor2D.y * 0.6, az);
    const imp = clamp(Number(node.importance || 0.5), 0, 1);
    const mesh = new THREE.Mesh(
      new THREE.SphereGeometry(isRoot ? 22 : 5 + imp * 9, 18, 18),
      new THREE.MeshStandardMaterial({ color: new THREE.Color(typeColor(node.type, dark)), metalness: 0.12, roughness: 0.42, emissive: 0x000000 })
    );
    mesh.position.copy(anchor); mesh.userData = { id, baseColor: mesh.material.color.clone() };
    threeScene.add(mesh); threeNodeMeshes.set(id, mesh);
    threeNodeMeta.set(id, { parentId: parentId || null, depth: d, anchor: anchor.clone(), velocity: new THREE.Vector3(), isRoot, importance: imp });
  }
  for (const link of links) {
    const source = threeNodeMeshes.get(link.source); const target = threeNodeMeshes.get(link.target);
    if (!source || !target) continue;
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([source.position.clone(), target.position.clone()]),
      new THREE.LineBasicMaterial({ color: link.logic_type === 'negative' ? 0xe74c3c : (dark ? 0x95a0ad : 0x7f8c8d), transparent: true, opacity: 0.75 })
    );
    threeScene.add(line); threeEdgeRefs.push({ line, sourceId: link.source, targetId: link.target });
  }
  refreshThreeStyles(); resizeThreeRenderer();
};

const refreshThreeStyles = () => {
  const dark = isDark();
  for (const [id, mesh] of threeNodeMeshes.entries()) {
    const node = safeNodes.value.find((n) => n.id === id); if (!node || !mesh.material) continue;
    mesh.material.color.set(typeColor(node.type, dark));
    const isActive = id === activeNodeId.value;
    mesh.material.emissive = new THREE.Color(isActive ? '#e74c3c' : '#000000');
    mesh.material.emissiveIntensity = isActive ? 0.8 : 0.0;
  }
};

const stepThreePhysics = () => {
  const ids = [...threeNodeMeshes.keys()]; if (ids.length <= 1) return;
  for (let i = 0; i < ids.length; i++) {
    const metaA = threeNodeMeta.get(ids[i]); const meshA = threeNodeMeshes.get(ids[i]);
    if (!meshA || !metaA || metaA.isRoot) continue;
    const force = new THREE.Vector3();
    force.add(metaA.anchor.clone().sub(meshA.position).multiplyScalar(0.03));
    force.add(meshA.position.clone().multiplyScalar(-0.0028));
    if (metaA.parentId && threeNodeMeshes.has(metaA.parentId)) {
      const delta = threeNodeMeshes.get(metaA.parentId).position.clone().sub(meshA.position);
      const dist = Math.max(delta.length(), 1); const targetLen = 48 + metaA.depth * 18;
      force.add(delta.normalize().multiplyScalar((dist - targetLen) * 0.055));
    }
    for (let j = 0; j < ids.length; j++) {
      if (i === j) continue;
      const meshB = threeNodeMeshes.get(ids[j]); if (!meshB) continue;
      const delta = meshA.position.clone().sub(meshB.position);
      force.add(delta.normalize().multiplyScalar(2200 / Math.max(delta.lengthSq(), 64)));
    }
    metaA.velocity.add(force.multiplyScalar(0.95)).multiplyScalar(0.88);
    const speed = metaA.velocity.length(); if (speed > 8) metaA.velocity.multiplyScalar(8 / speed);
    meshA.position.add(metaA.velocity);
  }
  for (const edge of threeEdgeRefs) {
    const s = threeNodeMeshes.get(edge.sourceId); const t = threeNodeMeshes.get(edge.targetId);
    if (s && t) edge.line.geometry.setFromPoints([s.position, t.position]);
  }
};

const onThreePointerDown = (event) => {
  if (!threeRenderer || !threeCamera || !threeRaycaster || !threePointer) return;
  const rect = threeRenderer.domElement.getBoundingClientRect(); if (!rect.width || !rect.height) return;
  threePointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  threePointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  threeRaycaster.setFromCamera(threePointer, threeCamera);
  const hit = threeRaycaster.intersectObjects([...threeNodeMeshes.values()], false)[0]?.object?.userData?.id;
  if (hit) { activeNodeId.value = hit; refreshThreeStyles(); }
};

const startThreeAnimation = () => {
  if (animationFrame || !threeRenderer || !threeScene || !threeCamera) return;
  const tick = () => {
    animationFrame = requestAnimationFrame(tick);
    if (activeView.value !== '3d') return;
    stepThreePhysics(); threeControls?.update(); threeRenderer.render(threeScene, threeCamera);
  };
  tick();
};

const stopThreeAnimation = () => { if (!animationFrame) return; cancelAnimationFrame(animationFrame); animationFrame = null; };

// ── tree view ──────────────────────────────────────────────────────────────
const treeRoots = computed(() => {
  const rootId = rootNodeId.value;
  return (graphHierarchy.value.children.get(rootId) || []).map((id) => nodeById.value.get(id)).filter(Boolean);
});

const treeChildren = (parentId) => {
  return (graphHierarchy.value.children.get(parentId) || []).map((id) => nodeById.value.get(id)).filter(Boolean);
};

// ── watchers & lifecycle ───────────────────────────────────────────────────
watch(
  () => [props.nodes, props.links, props.content, props.visualConfig, props.dynamicPayload],
  () => {
    if (!safeNodes.value.length) return;
    userExpandedClusterIds.value = new Set([...userExpandedClusterIds.value].filter((id) => clusterMetaMap.value.has(id)));
    graphZoom.value = clamp(Number(props.visualConfig?.initial_zoom ?? 1), 0.2, 2.8);
    if (!activeNodeId.value || !nodeById.value.has(activeNodeId.value)) {
      activeNodeId.value = props.visualConfig?.focus_node || rootNodeId.value || safeNodes.value[0].id;
    }
    nextTick(() => { render2DGraph(); rebuildThreeGraph(); });
  },
  { immediate: true, deep: true }
);

watch(activeView, (view) => {
  if (view !== '3d') stopThreeAnimation();
  if (view !== '2d') stopClusterFollowerSync();
  if (view === '2d') nextTick(() => { render2DGraph(); chart2D?.resize(); });
  if (view === '3d') nextTick(() => { rebuildThreeGraph(); startThreeAnimation(); });
});

watch(showJson, () => nextTick(() => { chart2D?.resize(); resizeThreeRenderer(); }));

onMounted(() => {
  if (safeNodes.value.length) activeNodeId.value = props.visualConfig?.focus_node || rootNodeId.value || safeNodes.value[0].id;
  render2DGraph(); rebuildThreeGraph();
  themeObserver = new MutationObserver(() => { render2DGraph(); refreshThreeStyles(); });
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  if (graph2DRef.value) {
    resizeObserver = new ResizeObserver(() => { chart2D?.resize(); resizeThreeRenderer(); });
    resizeObserver.observe(graph2DRef.value);
    if (graph3DRef?.value) resizeObserver.observe(graph3DRef.value);
  }
});

onBeforeUnmount(() => {
  stopThreeAnimation();
  stopClusterFollowerSync();
  threeRenderer?.domElement?.removeEventListener('pointerdown', onThreePointerDown);
  disposeThreeGraph(); threeControls?.dispose?.(); threeRenderer?.dispose?.();
  threeScene = threeCamera = threeControls = threeRenderer = null;
  chart2D?.dispose(); themeObserver?.disconnect(); resizeObserver?.disconnect();
});
</script>

<style scoped>
.kg-panel { display: flex; flex-direction: column; gap: 12px; min-height: 920px; }
.kg-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.kg-tabs { display: flex; gap: 8px; }
.kg-tab { background: #f3f3f3; border: 1px solid #e0e0e0; color: #444; padding: 6px 12px; font-size: 12px; cursor: pointer; }
.kg-tab.active { background: #111; color: #fff; border-color: #111; }
.kg-tab-disabled { background: #f3f3f3; border: 1px solid #e0e0e0; color: #bbb; padding: 6px 12px; font-size: 12px; cursor: not-allowed; }
.kg-actions { display: flex; align-items: center; gap: 10px; }
.kg-meta { display: flex; gap: 10px; color: #888; font-size: 12px; }
.kg-json-toggle { background: #fff; border: 1px solid #ddd; color: #333; padding: 6px 10px; font-size: 12px; cursor: pointer; }

.kg-content { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; min-height: 840px; }
.kg-content.json-open { grid-template-columns: minmax(0, 1fr) 360px; }
.kg-main { border: 1px solid #e6e6e6; background: #fff; min-height: 840px; position: relative; }

.graph-2d-wrapper { position: relative; width: 100%; height: 840px; display: flex; }
.graph-2d { flex: 1; height: 840px; }

/* ops panel */
.kg-ops-panel {
  width: 200px; flex-shrink: 0; border-left: 1px solid #ececec;
  padding: 12px 10px; display: flex; flex-direction: column; gap: 14px;
  background: #fafafa; box-sizing: border-box;
}
.kg-search {
  width: 100%; padding: 6px 12px; border-radius: 999px;
  border: 1px solid #ddd; font-size: 12px; outline: none; background: #fff;
  box-sizing: border-box;
}
.kg-search:focus { border-color: #3498db; }
.kg-depth-label { font-size: 11px; color: #888; margin-bottom: 6px; }
.kg-depth-buttons { display: flex; flex-wrap: wrap; gap: 5px; }
.kg-depth-btn {
  padding: 3px 9px; border-radius: 999px; border: 1.5px solid; font-size: 12px;
  cursor: pointer; background: transparent; transition: all 0.15s;
}
.kg-cluster-tip {
  border: 1px solid #ececec; border-radius: 10px; padding: 10px 10px 8px;
  background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(247,247,247,0.96));
}
.kg-cluster-copy { font-size: 12px; line-height: 1.6; color: #666; }

/* text / tree view */
.graph-text { width: 100%; height: 840px; overflow-y: auto; padding: 14px; box-sizing: border-box; }
.tree-list { display: flex; flex-direction: column; gap: 8px; }
.tree-node {
  background: #fff; border: 1px solid #e8e8e8; border-left: 3px solid;
  border-radius: 6px; padding: 8px 12px; font-size: 13px; color: #333;
}
.tree-summary { cursor: pointer; font-weight: 600; user-select: none; list-style: none; }
.tree-summary::-webkit-details-marker { display: none; }
.tree-summary::before { content: '▶ '; font-size: 10px; opacity: 0.6; }
details[open] > .tree-summary::before { content: '▼ '; }
.tree-children { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; padding-left: 12px; }
.tree-empty { white-space: pre-wrap; line-height: 1.7; color: #333; }

.kg-json { border: 1px solid #e6e6e6; background: #fafafa; min-height: 840px; display: flex; flex-direction: column; }
.kg-json-title { padding: 8px 12px; font-size: 12px; color: #666; border-bottom: 1px solid #ececec; flex-shrink: 0; }
.kg-json pre { margin: 0; padding: 10px 12px; overflow: auto; font-size: 12px; color: #555; flex: 1; }

.kg-legend { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.legend-item { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: #666; }
.legend-dot { width: 9px; height: 9px; border-radius: 50%; }

:deep(.kg-entity) { background: #fff2cd; border-radius: 4px; padding: 0 2px; }
:deep(.kg-entity.active) { background: #ffd8d2; outline: 1px solid #e74c3c; }

:global([data-theme="dark"]) .kg-main { background: #1f1f1f; border-color: #333; }
:global([data-theme="dark"]) .kg-tab { background: #1a1a1a; border-color: #333; color: #ddd; }
:global([data-theme="dark"]) .kg-tab.active { background: #c0392b; border-color: #c0392b; }
:global([data-theme="dark"]) .kg-tab-disabled { background: #1a1a1a; border-color: #333; color: #555; }
:global([data-theme="dark"]) .kg-json-toggle { background: #1a1a1a; border-color: #333; color: #ddd; }
:global([data-theme="dark"]) .kg-meta { color: #bbb; }
:global([data-theme="dark"]) .kg-ops-panel { background: #1a1a1a; border-color: #333; }
:global([data-theme="dark"]) .kg-search { background: #111; border-color: #444; color: #eee; }
:global([data-theme="dark"]) .kg-cluster-tip { background: linear-gradient(180deg, rgba(37,37,37,0.94), rgba(28,28,28,0.98)); border-color: #333; }
:global([data-theme="dark"]) .kg-cluster-copy { color: #b8b8b8; }
:global([data-theme="dark"]) .tree-node { background: #1e1e1e; border-color: #333; color: #eee; }
:global([data-theme="dark"]) .tree-empty { color: #ececec; }
:global([data-theme="dark"]) .graph-text { color: #ececec; }
:global([data-theme="dark"]) .kg-json { background: #1b1b1b; border-color: #333; }
:global([data-theme="dark"]) .kg-json-title { color: #ccc; border-color: #333; }
:global([data-theme="dark"]) .kg-json pre { color: #d8d8d8; }
:global([data-theme="dark"]) .legend-item { color: #cfcfcf; }
:global([data-theme="dark"]) .kg-entity { background: #3f3320; }
:global([data-theme="dark"]) .kg-entity.active { background: #5a2b31; outline-color: #e74c3c; }

@media (max-width: 1280px) {
  .kg-content.json-open { grid-template-columns: minmax(0, 1fr); }
  .kg-json { min-height: 260px; }
  .kg-ops-panel { width: 160px; }
}
</style>
