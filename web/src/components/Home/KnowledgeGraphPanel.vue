<template>
  <div class="kg-panel">
    <div class="kg-toolbar">
      <div class="kg-tabs">
        <button class="kg-tab" :class="{ active: activeView === '2d' }" @click="activeView = '2d'">二维知识图谱</button>
        <button class="kg-tab" :class="{ active: activeView === '3d' }" @click="activeView = '3d'">三维知识图谱球</button>
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
        <div v-show="activeView === '2d'" ref="graph2DRef" class="graph-2d"></div>
        <canvas v-show="activeView === '3d'" ref="graph3DRef" class="graph-3d" @click="handle3DClick"></canvas>
        <div v-show="activeView === 'text'" ref="textRef" class="graph-text" v-html="highlightedText"></div>
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
const graph2DRef = ref(null);
const graph3DRef = ref(null);
const textRef = ref(null);
const graphZoom = ref(1);

let chart2D = null;
let themeObserver = null;
let resizeObserver = null;
let animationFrame = null;

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
  if (text.includes('�')) return true;
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
  const line = String(text || '')
    .split(/\r?\n/)
    .map((s) => s.trim())
    .find(Boolean);
  return shorten(line || '', 80);
};

const pickPayloadTitle = (payload) => {
  const visited = new Set();
  const walk = (obj, depth = 0) => {
    if (!obj || depth > 4 || visited.has(obj)) return '';
    if (typeof obj === 'string') {
      const s = shorten(obj, 80);
      if (s && !isGenericRootLabel(s)) return s;
      return '';
    }
    if (Array.isArray(obj)) {
      for (const item of obj.slice(0, 20)) {
        const hit = walk(item, depth + 1);
        if (hit) return hit;
      }
      return '';
    }
    if (typeof obj === 'object') {
      visited.add(obj);
      for (const [k, v] of Object.entries(obj).slice(0, 40)) {
        if (typeof v === 'string') {
          const s = shorten(v, 80);
          if (s && !isGenericRootLabel(s)) return s;
        }
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
    主题: dark ? '#ff8b82' : '#c0392b',
    对象: dark ? '#8fb2ff' : '#2f6fdd',
    流程: dark ? '#7cd1ff' : '#1f97c9',
    材料: dark ? '#a9d07b' : '#4f8f2f',
    时间: dark ? '#ffd38f' : '#d18b27',
    约束: dark ? '#c9a2ff' : '#8c57d1',
    风险: dark ? '#ff9cab' : '#d94f68',
    实体: dark ? '#aab3c2' : '#6c7a89',
  };
  return map[type] || (dark ? '#91a5ff' : '#356fe0');
};

const baseNodes = computed(() =>
  (props.nodes || [])
    .map((item, idx) => ({
      id: String(item?.id || `node_${idx + 1}`),
      label: sanitizeNodeLabel(item?.label, `节点${idx + 1}`),
      type: String(item?.type || '实体'),
      importance: clamp(Number(item?.importance ?? 0.5), 0, 1),
      layer: item?.layer ? String(item.layer) : '',
      group: item?.group ? String(item.group) : '',
      parent_id: item?.parent_id ? String(item.parent_id) : null,
    }))
    .filter((item) => item.label)
);

const baseLinks = computed(() =>
  (props.links || [])
    .map((item) => ({
      source: String(item?.source || ''),
      target: String(item?.target || ''),
      relation: (() => {
        const raw = shorten(String(item?.relation || '关联'), 20);
        return /^(展开|包含|值|关联)$/i.test(raw) ? '' : raw;
      })(),
      logic_type: String(item?.logic_type || 'positive'),
      strength: clamp(Number(item?.strength ?? 0.6), 0, 1),
    }))
    .filter((item) => item.source && item.target)
);

const safeNodes = computed(() => {
  return baseNodes.value;
});

const rootNodeId = computed(() => {
  if (!safeNodes.value.length) return null;
  // Core rule (DO NOT CHANGE):
  // Frontend must NOT infer semantics from fixed content fields like topic/summary/title.
  // Root selection can only use generic graph signals (focus id / importance / order).
  const focusId = String(props.visualConfig?.focus_node || '').trim();
  if (focusId) {
    const byFocus = safeNodes.value.find((n) => n.id === focusId);
    if (byFocus) return byFocus.id;
  }

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
  String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

const highlightedText = computed(() => {
  const content = props.content || '';
  const ranges = Object.entries(textMapping.value)
    .map(([nodeId, range]) => {
      if (!Array.isArray(range) || range.length < 2) return null;
      const start = Number(range[0]);
      const end = Number(range[1]);
      if (!Number.isFinite(start) || !Number.isFinite(end) || start < 0 || end <= start || end > content.length) {
        return null;
      }
      return { nodeId, start, end };
    })
    .filter(Boolean)
    .sort((a, b) => a.start - b.start);

  if (!ranges.length) return escapeHtml(content);

  let cursor = 0;
  let html = '';
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

const hashSeed = (text) => {
  let hash = 2166136261;
  const value = String(text || '');
  for (let i = 0; i < value.length; i += 1) {
    hash ^= value.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return Math.abs(hash >>> 0);
};

const refresh2DStyles = () => {
  if (!chart2D) return;
  const option = chart2D.getOption?.();
  const series = option?.series?.[0];
  if (!series?.data) return;
  const dark = isDark();
  const rootId = rootNodeId.value;
  const nextData = series.data.map((item) => {
    const id = String(item?.id || '');
    const src = safeNodes.value.find((n) => n.id === id);
    const isRoot = id === rootId;
    return {
      ...item,
      name: isRoot ? documentTitle.value : (src?.label || item?.name || ''),
      itemStyle: {
        ...(item?.itemStyle || {}),
        color: id === activeNodeId.value ? '#e74c3c' : typeColor(src?.type || '实体', dark),
      },
      label: {
        ...(item?.label || {}),
        show: shouldShowNodeLabel(src || { id, importance: 0.5 }),
        color: dark ? '#f2f2f2' : '#333',
        fontSize: isRoot ? 14 : 12,
        fontWeight: isRoot ? 700 : 400,
      },
    };
  });
  chart2D.setOption({
    series: [{ id: 'kg_main_graph', data: nextData }],
  });
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
    for (const c of children) {
      if (parent.has(c)) continue;
      parent.set(c, cur);
      queue.push(c);
    }
  }
  for (const id of nodeIds) {
    if (!parent.has(id)) parent.set(id, rootId);
  }

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
    let x = x0;
    let y = y0;
    let r = 0;
    let ang = ((seed % 360) * Math.PI) / 180;
    for (let k = 0; k < 80; k += 1) {
      const overlap = placed.some((p) => Math.hypot(p.x - x, p.y - y) < minDist);
      if (!overlap) break;
      r += 10;
      ang += 1.618;
      x = x0 + Math.cos(ang) * r;
      y = y0 + Math.sin(ang) * r;
    }
    placed.push({ x, y });
    return { x, y };
  };

  map.set(rootId, { x: 0, y: 0 });
  placed.push({ x: 0, y: 0 });

  const walk = (pid, depth) => {
    const children = childrenMap.get(pid) || [];
    if (!children.length) return;
    const p = map.get(pid) || { x: 0, y: 0 };
    const n = children.length;
    const base = 120 + depth * 34;
    const offset = (hashSeed(pid) % 360) * (Math.PI / 180);
    children.forEach((cid, idx) => {
      const angle = offset + (Math.PI * 2 * idx) / n;
      const candX = p.x + Math.cos(angle) * base;
      const candY = p.y + Math.sin(angle) * base;
      const pos = placeAvoid(candX, candY, hashSeed(cid));
      map.set(cid, pos);
      walk(cid, depth + 1);
    });
  };
  walk(rootId, 1);
  return map;
};

const render2DGraph = () => {
  if (!graph2DRef.value) return;
  if (!chart2D) {
    chart2D = echarts.init(graph2DRef.value);
  }

  const dark = isDark();
  const rootId = rootNodeId.value;
  const posMap = buildTreeLayout(safeNodes.value, safeLinks.value, rootId);

  const nodeData = safeNodes.value.map((node) => {
    const isRoot = node.id === rootId;
    const imp = clamp(Number(node.importance || 0.5), 0, 1);
    const symbolSize = isRoot ? 56 : 12 + imp * 28;
    const pos = posMap.get(node.id) || { x: 0, y: 0 };
    return {
      id: node.id,
      name: (isRoot ? documentTitle.value : node.label),
      value: node.type,
      x: pos.x,
      y: pos.y,
      fixed: isRoot,
      symbolSize,
      draggable: false,
      itemStyle: {
        color: node.id === activeNodeId.value ? '#e74c3c' : typeColor(node.type, dark),
      },
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
    source: link.source,
    target: link.target,
    value: link.relation,
    lineStyle: {
      color: link.logic_type === 'negative' ? '#e74c3c' : dark ? '#9da5b3' : '#7f8c8d',
      type: link.logic_type === 'negative' ? 'dashed' : 'solid',
      width: 0.7 + clamp(Number(link.strength || 0.6), 0, 1) * 2.2,
      opacity: 0.85,
    },
    label: {
      show: shouldShowEdgeLabel(link),
      formatter: () => shorten(link.relation, 10),
      color: dark ? '#d6d6d6' : '#666',
      fontSize: 10,
    },
  }));

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
        return `${params.name}<br/>${params.data.value || ''}`;
      },
    },
    series: [
      {
        id: 'kg_main_graph',
        type: 'graph',
        layout: 'force',
        layoutAnimation: true,
        roam: true,
        zoom: clamp(graphZoom.value || 1, 0.2, 2.8),
        data: nodeData,
        links: edgeData,
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: 8,
        force: {
          repulsion: [160, 340],
          gravity: 0.06,
          edgeLength: [90, 175],
          friction: 0.86,
          layoutAnimation: true,
        },
      },
    ],
  });

  chart2D.off('click');
  chart2D.on('click', (params) => {
    if (params.dataType === 'node' && params.data?.id) {
      setActiveNode(params.data.id);
    }
  });

  chart2D.off('graphRoam');
  chart2D.on('graphRoam', () => {
    const option = chart2D?.getOption?.();
    const z = Number(option?.series?.[0]?.zoom || 1);
    graphZoom.value = clamp(z, 0.2, 2.8);
  });
};

const projectPoint = (point, width, height, angle) => {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const x = point.x * cos - point.z * sin;
  const z = point.x * sin + point.z * cos;
  const y = point.y;
  const perspective = 1.35;
  const scale = perspective / (perspective - z);
  return {
    x: x * scale * width * 0.22 + width / 2,
    y: y * scale * height * 0.22 + height / 2,
    z,
  };
};

const spherePoints = ref([]);
const projectedPoints = ref([]);
const rotation = ref(0);

const rebuildSphere = () => {
  const count = Math.max(safeNodes.value.length, 1);
  const points = [];
  for (let i = 0; i < count; i += 1) {
    const y = 1 - (i / (count - 1 || 1)) * 2;
    const radius = Math.sqrt(Math.max(0, 1 - y * y));
    const theta = Math.PI * (3 - Math.sqrt(5)) * i;
    points.push({
      x: Math.cos(theta) * radius,
      y,
      z: Math.sin(theta) * radius,
    });
  }
  spherePoints.value = points;
};

const render3D = () => {
  const canvas = graph3DRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return;

  canvas.width = rect.width * window.devicePixelRatio;
  canvas.height = rect.height * window.devicePixelRatio;
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

  const dark = isDark();
  ctx.clearRect(0, 0, rect.width, rect.height);

  projectedPoints.value = spherePoints.value.map((point, idx) => ({
    ...projectPoint(point, rect.width, rect.height, rotation.value),
    node: safeNodes.value[idx],
  }));

  for (const link of safeLinks.value) {
    const from = projectedPoints.value.find((item) => item.node?.id === link.source);
    const to = projectedPoints.value.find((item) => item.node?.id === link.target);
    if (!from || !to) continue;
    ctx.beginPath();
    ctx.setLineDash(link.logic_type === 'negative' ? [5, 4] : []);
    ctx.strokeStyle = link.logic_type === 'negative' ? '#e74c3c' : dark ? '#8c8f95' : '#9aa3ad';
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();
  }
  ctx.setLineDash([]);

  const sorted = [...projectedPoints.value].sort((a, b) => a.z - b.z);
  for (const item of sorted) {
    const isRoot = item.node?.id === rootNodeId.value;
    const imp = clamp(Number(item.node?.importance || 0.5), 0, 1);
    const size = isRoot ? 14 : 4 + imp * 8;
    ctx.beginPath();
    ctx.arc(item.x, item.y, size, 0, Math.PI * 2);
    const isActive = item.node?.id === activeNodeId.value;
    ctx.fillStyle = isActive ? '#e74c3c' : typeColor(item.node?.type, dark);
    ctx.fill();

    if (isRoot || imp >= 0.75) {
      ctx.font = isRoot ? 'bold 13px sans-serif' : '12px sans-serif';
      ctx.fillStyle = dark ? '#f0f0f0' : '#333';
      const label = shorten(item.node?.label || '', isRoot ? 30 : 16);
      ctx.fillText(label, item.x + size + 3, item.y + 3);
    }
  }

  rotation.value += 0.0045;
  animationFrame = requestAnimationFrame(render3D);
};

const setActiveNode = (nodeId) => {
  activeNodeId.value = nodeId;
  if (activeView.value === 'text') {
    nextTick(() => {
      document.getElementById(`kg-anchor-${nodeId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  }
  refresh2DStyles();
};

const handle3DClick = (event) => {
  const rect = graph3DRef.value?.getBoundingClientRect();
  if (!rect) return;
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  let hit = null;
  let minDist = 14;
  for (const point of projectedPoints.value) {
    const dist = Math.hypot(point.x - x, point.y - y);
    if (dist < minDist) {
      minDist = dist;
      hit = point;
    }
  }
  if (hit?.node?.id) setActiveNode(hit.node.id);
};

watch(
  () => [props.nodes, props.links, props.content, props.visualConfig, props.dynamicPayload],
  () => {
    if (!safeNodes.value.length) return;
    graphZoom.value = clamp(Number(props.visualConfig?.initial_zoom ?? 1), 0.2, 2.8);
    if (!activeNodeId.value) {
      activeNodeId.value = props.visualConfig?.focus_node || rootNodeId.value || safeNodes.value[0].id;
    }
    rebuildSphere();
    nextTick(() => {
      render2DGraph();
    });
  },
  { immediate: true, deep: true }
);

watch(activeView, (view) => {
  if (view === 'text' && activeNodeId.value) {
    nextTick(() => {
      document.getElementById(`kg-anchor-${activeNodeId.value}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  }
  if (view === '2d') {
    nextTick(() => {
      render2DGraph();
      chart2D?.resize();
    });
  }
});

watch(showJson, () => {
  nextTick(() => {
    chart2D?.resize();
  });
});

onMounted(() => {
  if (safeNodes.value.length) {
    activeNodeId.value = props.visualConfig?.focus_node || rootNodeId.value || safeNodes.value[0].id;
  }
  rebuildSphere();
  render2DGraph();
  render3D();

  themeObserver = new MutationObserver(() => {
    render2DGraph();
  });
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme'],
  });

  if (graph2DRef.value) {
    resizeObserver = new ResizeObserver(() => {
      chart2D?.resize();
    });
    resizeObserver.observe(graph2DRef.value);
  }
});

onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrame);
  chart2D?.dispose();
  themeObserver?.disconnect();
  resizeObserver?.disconnect();
});
</script>

<style scoped>
.kg-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 920px;
}

.kg-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.kg-tabs {
  display: flex;
  gap: 8px;
}

.kg-tab {
  background: #f3f3f3;
  border: 1px solid #e0e0e0;
  color: #444;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
}

.kg-tab.active {
  background: #111;
  color: #fff;
  border-color: #111;
}

.kg-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.kg-meta {
  display: flex;
  gap: 10px;
  color: #888;
  font-size: 12px;
}

.kg-json-toggle {
  background: #fff;
  border: 1px solid #ddd;
  color: #333;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
}

.kg-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
  min-height: 840px;
}

.kg-content.json-open {
  grid-template-columns: minmax(0, 1fr) 360px;
}

.kg-main {
  border: 1px solid #e6e6e6;
  background: #fff;
  min-height: 840px;
  position: relative;
}

.graph-2d,
.graph-3d,
.graph-text {
  width: 100%;
  height: 840px;
}

.graph-text {
  overflow-y: auto;
  padding: 14px;
  box-sizing: border-box;
  white-space: pre-wrap;
  line-height: 1.7;
  color: #333;
}

:deep(.kg-entity) {
  background: #fff2cd;
  border-radius: 4px;
  padding: 0 2px;
}

:deep(.kg-entity.active) {
  background: #ffd8d2;
  outline: 1px solid #e74c3c;
}

.kg-json {
  border: 1px solid #e6e6e6;
  background: #fafafa;
  min-height: 840px;
  display: flex;
  flex-direction: column;
}

.kg-json-title {
  padding: 8px 12px;
  font-size: 12px;
  color: #666;
  border-bottom: 1px solid #ececec;
  flex-shrink: 0;
}

.kg-json pre {
  margin: 0;
  padding: 10px 12px;
  overflow: auto;
  font-size: 12px;
  color: #555;
  flex: 1;
}

.kg-legend {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
}

.legend-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

:global([data-theme="dark"]) .kg-main {
  background: #1f1f1f;
  border-color: #333;
}

:global([data-theme="dark"]) .kg-tab {
  background: #1a1a1a;
  border-color: #333;
  color: #ddd;
}

:global([data-theme="dark"]) .kg-tab.active {
  background: #c0392b;
  border-color: #c0392b;
}

:global([data-theme="dark"]) .kg-json-toggle {
  background: #1a1a1a;
  border-color: #333;
  color: #ddd;
}

:global([data-theme="dark"]) .kg-meta {
  color: #bbb;
}

:global([data-theme="dark"]) .graph-text {
  color: #ececec;
}

:global([data-theme="dark"]) .kg-json {
  background: #1b1b1b;
  border-color: #333;
}

:global([data-theme="dark"]) .kg-json-title {
  color: #ccc;
  border-color: #333;
}

:global([data-theme="dark"]) .kg-json pre {
  color: #d8d8d8;
}

:global([data-theme="dark"]) .legend-item {
  color: #cfcfcf;
}

:global([data-theme="dark"]) .kg-entity {
  background: #3f3320;
}

:global([data-theme="dark"]) .kg-entity.active {
  background: #5a2b31;
  outline-color: #e74c3c;
}

@media (max-width: 1280px) {
  .kg-content.json-open {
    grid-template-columns: minmax(0, 1fr);
  }

  .kg-json {
    min-height: 260px;
  }
}
</style>
