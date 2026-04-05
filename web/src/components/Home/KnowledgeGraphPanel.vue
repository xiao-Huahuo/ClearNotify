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
          <span>节点 {{ safeNodes.length }}</span>
          <span>关系 {{ safeLinks.length }}</span>
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
const graph2DRef = ref(null);
const graph3DRef = ref(null);
const graphZoom = ref(1);
const searchQuery = ref('');
const filterDepth = ref(null);

let chart2D = null;
let themeObserver = null;
let resizeObserver = null;
let animationFrame = null;

const DEPTH_COLORS = ['#e74c3c','#f1c40f','#2ecc71','#3498db','#9b59b6','#e67e22','#1abc9c'];
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

const nodeTypes = computed(() => {
  const all = safeNodes.value.map((item) => item.type).filter(Boolean);
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
  return { parent, depth };
};

// ── tree layout ────────────────────────────────────────────────────────────
const hashSeed = (text) => {
  let hash = 2166136261;
  const value = String(text || '');
  for (let i = 0; i < value.length; i++) { hash ^= value.charCodeAt(i); hash = Math.imul(hash, 16777619); }
  return Math.abs(hash >>> 0);
};

const buildTreeLayout = (nodes, links, rootId) => {
  const map = new Map();
  if (!nodes.length || !rootId) return map;
  const nodeIds = new Set(nodes.map((n) => n.id));
  const adj = new Map();
  const addAdj = (s, t) => {
    if (!nodeIds.has(s) || !nodeIds.has(t) || s === t) return;
    if (!adj.has(s)) adj.set(s, []);
    if (!adj.get(s).includes(t)) adj.get(s).push(t);
  };
  for (const n of nodes) {
    if (n.parent_id && nodeIds.has(n.parent_id) && n.parent_id !== n.id) addAdj(n.parent_id, n.id);
  }
  for (const e of links) addAdj(e.source, e.target);
  const parent = new Map();
  const queue = [rootId];
  parent.set(rootId, null);
  while (queue.length) {
    const cur = queue.shift();
    const children = [...(adj.get(cur) || [])].sort((a, b) => a.localeCompare(b));
    for (const c of children) { if (parent.has(c)) continue; parent.set(c, cur); queue.push(c); }
  }
  for (const id of nodeIds) { if (!parent.has(id)) parent.set(id, rootId); }
  const childrenMap = new Map();
  for (const [id, p] of parent.entries()) {
    if (p === null) continue;
    if (!childrenMap.has(p)) childrenMap.set(p, []);
    childrenMap.get(p).push(id);
  }
  for (const arr of childrenMap.values()) arr.sort((a, b) => a.localeCompare(b));
  const placed = [];
  const minDist = 56;
  const placeAvoid = (x0, y0, seed) => {
    let x = x0, y = y0, r = 0, ang = ((seed % 360) * Math.PI) / 180;
    for (let k = 0; k < 80; k++) {
      if (!placed.some((p) => Math.hypot(p.x - x, p.y - y) < minDist)) break;
      r += 10; ang += 1.618; x = x0 + Math.cos(ang) * r; y = y0 + Math.sin(ang) * r;
    }
    placed.push({ x, y }); return { x, y };
  };
  map.set(rootId, { x: 0, y: 0 }); placed.push({ x: 0, y: 0 });
  const walk = (pid, depth) => {
    const children = childrenMap.get(pid) || [];
    if (!children.length) return;
    const p = map.get(pid) || { x: 0, y: 0 };
    const n = children.length;
    const base = 120 + depth * 34;
    const offset = (hashSeed(pid) % 360) * (Math.PI / 180);
    children.forEach((cid, idx) => {
      const angle = offset + (Math.PI * 2 * idx) / n;
      const pos = placeAvoid(p.x + Math.cos(angle) * base, p.y + Math.sin(angle) * base, hashSeed(cid));
      map.set(cid, pos); walk(cid, depth + 1);
    });
  };
  walk(rootId, 1);
  return map;
};

// ── depth filter helpers ───────────────────────────────────────────────────
const depthMapCache = ref(new Map());

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
  const adj = new Map();
  for (const link of safeLinks.value) {
    if (!adj.has(link.source)) adj.set(link.source, []);
    adj.get(link.source).push(link.target);
  }
  const result = new Set();
  const queue = [nodeId];
  while (queue.length) {
    const cur = queue.shift();
    for (const child of (adj.get(cur) || [])) {
      if (!result.has(child)) { result.add(child); queue.push(child); }
    }
  }
  return result;
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

const applyHighlightOverlay = () => {
  if (!chart2D) return;
  const option = chart2D.getOption?.();
  const series = option?.series?.[0];
  if (!series?.data) return;
  const dark = isDark();
  const rootId = rootNodeId.value;
  const hlId = highlightedNodeId.value;
  const searchQ = searchQuery.value.trim().toLowerCase();
  const descendants = hlId ? getDescendants(hlId) : null;

  const nextData = series.data.map((item) => {
    const id = String(item?.id || '');
    const src = safeNodes.value.find((n) => n.id === id);
    const d = Number(depthMapCache.value.get(id) ?? 0);
    const isRoot = id === rootId;
    const baseCol = depthColor(d);

    // search match
    const matchesSearch = searchQ && src?.label?.toLowerCase().startsWith(searchQ);
    // depth filter match
    const matchesDepth = filterDepth.value !== null && d === filterDepth.value;

    let color = baseCol;
    let opacity = 1;
    let borderWidth = 0;
    let borderColor = 'transparent';
    let labelShow = shouldShowNodeLabel(src || { id, importance: 0.5 });

    if (hlId) {
      if (id === hlId) {
        color = baseCol; borderWidth = 4; borderColor = '#fff'; opacity = 1;
      } else if (descendants?.has(id)) {
        opacity = 0.85;
      } else {
        opacity = 0.15; labelShow = false;
      }
    } else if (matchesSearch || matchesDepth) {
      borderWidth = 3; borderColor = '#fff'; opacity = 1;
    } else if (searchQ || filterDepth.value !== null) {
      opacity = 0.2; labelShow = false;
    }

    return {
      ...item,
      name: isRoot ? documentTitle.value : (src?.label || item?.name || ''),
      itemStyle: { color, opacity, borderWidth, borderColor },
      label: { ...item.label, show: labelShow, color: dark ? '#f2f2f2' : '#333', fontSize: isRoot ? 14 : 12, fontWeight: isRoot ? 700 : 400 },
    };
  });

  chart2D.setOption({ series: [{ id: 'kg_main_graph', data: nextData }] });
};

const onSearch = () => {
  highlightedNodeId.value = null;
  filterDepth.value = null;
  applyHighlightOverlay();
};

const clearHighlight = () => {
  highlightedNodeId.value = null;
  searchQuery.value = '';
  filterDepth.value = null;
  applyHighlightOverlay();
};

const render2DGraph = () => {
  if (!graph2DRef.value) return;
  if (!chart2D) chart2D = echarts.init(graph2DRef.value);
  const dark = isDark();
  const rootId = rootNodeId.value;
  const posMap = buildTreeLayout(safeNodes.value, safeLinks.value, rootId);
  const { depth } = buildParentDepthMap(safeNodes.value, safeLinks.value, rootId);
  depthMapCache.value = depth;

  const nodeData = safeNodes.value.map((node) => {
    const isRoot = node.id === rootId;
    const imp = clamp(Number(node.importance || 0.5), 0, 1);
    const symbolSize = isRoot ? 56 : 12 + imp * 28;
    const pos = posMap.get(node.id) || { x: 0, y: 0 };
    const d = Number(depth.get(node.id) ?? 0);
    return {
      id: node.id,
      name: isRoot ? documentTitle.value : node.label,
      value: node.type,
      x: pos.x, y: pos.y,
      fixed: isRoot,
      symbolSize,
      draggable: !isRoot,
      itemStyle: { color: depthColor(d), opacity: 1, borderWidth: 0, borderColor: 'transparent' },
      label: {
        show: shouldShowNodeLabel(node),
        color: dark ? '#f2f2f2' : '#333',
        fontSize: isRoot ? 14 : 12,
        fontWeight: isRoot ? 700 : 400,
        formatter: () => shorten(isRoot ? documentTitle.value : node.label, isRoot ? 38 : 22),
      },
    };
  });

  const edgeData = safeLinks.value.map((link) => ({
    source: link.source, target: link.target, value: link.relation,
    lineStyle: {
      color: link.logic_type === 'negative' ? '#e74c3c' : dark ? '#9da5b3' : '#7f8c8d',
      type: link.logic_type === 'negative' ? 'dashed' : 'solid',
      width: 0.7 + clamp(Number(link.strength || 0.6), 0, 1) * 2.2,
      opacity: 0.85,
    },
    label: { show: shouldShowEdgeLabel(link), formatter: () => shorten(link.relation, 10), color: dark ? '#d6d6d6' : '#666', fontSize: 10 },
  }));

  chart2D.setOption({
    backgroundColor: 'transparent',
    animationDurationUpdate: 350,
    tooltip: {
      trigger: 'item',
      backgroundColor: dark ? 'rgba(20,20,20,0.95)' : 'rgba(255,255,255,0.95)',
      borderColor: dark ? '#444' : '#ddd',
      textStyle: { color: dark ? '#f2f2f2' : '#333' },
      formatter: (params) => params.dataType === 'edge' ? `${params.data.value || '关系'}` : `${params.name}<br/>${params.data.value || ''}`,
    },
    series: [{
      id: 'kg_main_graph', type: 'graph', layout: 'force', layoutAnimation: true, roam: true,
      zoom: clamp(graphZoom.value || 1, 0.2, 2.8),
      data: nodeData, links: edgeData,
      edgeSymbol: ['none', 'arrow'], edgeSymbolSize: 8,
      force: { repulsion: [160, 340], gravity: 0.06, edgeLength: [90, 175], friction: 0.86, layoutAnimation: true },
    }],
  });

  chart2D.off('click');
  chart2D.on('click', (params) => {
    if (params.dataType === 'node' && params.data?.id) {
      const id = params.data.id;
      if (highlightedNodeId.value === id) { clearHighlight(); return; }
      highlightedNodeId.value = id;
      activeNodeId.value = id;
      searchQuery.value = '';
      filterDepth.value = null;
      applyHighlightOverlay();
    } else if (params.dataType !== 'edge') {
      clearHighlight();
    }
  });

  chart2D.off('graphRoam');
  chart2D.on('graphRoam', () => {
    const option = chart2D?.getOption?.();
    const z = Number(option?.series?.[0]?.zoom || 1);
    graphZoom.value = clamp(z, 0.2, 2.8);
  });
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
  return safeNodes.value.filter((n) => {
    const d = depthMapCache.value.get(n.id);
    return d === 1 || (d === undefined && n.id !== rootId);
  });
});

const treeChildren = (parentId) => {
  const childIds = new Set(safeLinks.value.filter((l) => l.source === parentId).map((l) => l.target));
  return safeNodes.value.filter((n) => childIds.has(n.id));
};

// ── watchers & lifecycle ───────────────────────────────────────────────────
watch(
  () => [props.nodes, props.links, props.content, props.visualConfig, props.dynamicPayload],
  () => {
    if (!safeNodes.value.length) return;
    graphZoom.value = clamp(Number(props.visualConfig?.initial_zoom ?? 1), 0.2, 2.8);
    if (!activeNodeId.value) activeNodeId.value = props.visualConfig?.focus_node || rootNodeId.value || safeNodes.value[0].id;
    nextTick(() => { render2DGraph(); rebuildThreeGraph(); });
  },
  { immediate: true, deep: true }
);

watch(activeView, (view) => {
  if (view !== '3d') stopThreeAnimation();
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
