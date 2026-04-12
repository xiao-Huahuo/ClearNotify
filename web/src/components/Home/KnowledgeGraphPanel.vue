<template>
  <div ref="panelRef" class="kg-panel" :class="{ 'is-fullscreen': isFullscreen }">
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
        <button v-if="activeView === '2d'" class="kg-toolbar-btn" @click="toggleFullscreen">{{ isFullscreen ? '退出全屏' : '图谱全屏' }}</button>
        <button class="kg-toolbar-btn" @click="showJson = !showJson">{{ showJson ? '隐藏 JSON' : '显示 JSON' }}</button>
      </div>
    </div>

    <div class="kg-content" :class="{ 'json-open': showJson }">
      <div class="kg-main">
        <div v-show="activeView === '2d'" ref="graph2DWrapperRef" class="graph-2d-wrapper">
          <div ref="graph2DRef" class="graph-2d" @click.self="clearHighlight"></div>
          <div
            v-if="selectedGlowState.visible"
            class="kg-selected-gloss"
            :style="selectedGlowStyle"
            aria-hidden="true"
          ></div>
          <div class="kg-ops-panel">
            <template v-if="sidePanelMode === 'query'">
              <div class="kg-side-kicker">图谱查询</div>
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
              <div v-if="personalRecommendation" class="kg-panel-section kg-persona-panel" :class="recommendationToneClass">
                <div class="kg-section-heading kg-persona-heading">
                  <div>
                    <div class="kg-depth-label">个性需求推荐</div>
                    <div class="kg-cluster-copy">{{ recommendationSummary }}</div>
                  </div>
                  <div class="kg-persona-score">
                    <strong>{{ recommendationScore }}</strong>
                    <span>{{ recommendationPriority }}</span>
                  </div>
                </div>
                <div v-if="recommendationProfileLabel" class="kg-persona-meta">
                  <span class="kg-source-pill">{{ recommendationProfileLabel }}</span>
                </div>
                <div v-if="recommendationKeywords.length" class="kg-persona-tags">
                  <span v-for="keyword in recommendationKeywords" :key="keyword" class="kg-persona-tag">{{ keyword }}</span>
                </div>
                <div v-if="recommendationReasons.length" class="kg-persona-block">
                  <div class="kg-depth-label">推荐理由</div>
                  <ul class="kg-persona-list">
                    <li v-for="reason in recommendationReasons" :key="reason">{{ reason }}</li>
                  </ul>
                </div>
                <div v-if="recommendationSuggestions.length" class="kg-persona-block">
                  <div class="kg-depth-label">建议动作</div>
                  <ul class="kg-persona-list is-action">
                    <li v-for="suggestion in recommendationSuggestions" :key="suggestion">{{ suggestion }}</li>
                  </ul>
                </div>
              </div>
              <div v-if="rewriteTargetsSafe.length" class="kg-panel-section">
                <div class="kg-section-heading">
                  <div>
                    <div class="kg-depth-label">转译版本</div>
                    <div class="kg-cluster-copy">将当前解析结果改写成不同对象更容易理解的版本。</div>
                  </div>
                  <span v-if="rewriteLoading" class="kg-inline-status">正在生成...</span>
                </div>
                <div class="kg-rewrite-grid">
                  <button
                    v-for="target in rewriteTargetsSafe"
                    :key="target"
                    class="kg-rewrite-btn"
                    :disabled="!rewriteEnabled || rewriteLoading"
                    @click="triggerRewrite(target)"
                  >{{ target }}</button>
                </div>
              </div>
            </template>

            <template v-else>
              <div class="kg-source-panel">
                <div class="kg-source-header">
                  <div>
                    <div class="kg-side-kicker">原文对照</div>
                    <div class="kg-source-title">{{ activeSourceNodeTitle }}</div>
                  </div>
                  <button class="kg-back-btn" @click="switchToQueryPanel">返回查询</button>
                </div>

                <div class="kg-source-meta">
                  <span v-if="selectedNode?.type" class="kg-source-pill">{{ selectedNode.type }}</span>
                  <span v-if="selectedNodeDepth !== null" class="kg-source-pill">深度 {{ selectedNodeDepth }}</span>
                  <a
                    v-if="originalFileUrl"
                    class="kg-source-link"
                    :href="originalFileUrl"
                    target="_blank"
                    rel="noreferrer"
                  >查看原文件</a>
                </div>

                <div class="kg-source-notice">{{ activeSourceNotice }}</div>

                <div class="kg-panel-section">
                  <div class="kg-depth-label">父节点</div>
                  <div v-if="selectedParentNode" class="kg-node-chip-list">
                    <button class="kg-node-chip" @click="focusNodeFromSidebar(selectedParentNode.id)">{{ formatNodeLabel(selectedParentNode) }}</button>
                  </div>
                  <div v-else class="kg-empty-hint">当前节点已经是根节点。</div>
                </div>

                <div class="kg-panel-section">
                  <div class="kg-section-heading">
                    <div class="kg-depth-label">子节点</div>
                    <span v-if="selectedChildNodes.length" class="kg-inline-status">{{ selectedChildNodes.length }} 个</span>
                  </div>
                  <div v-if="visibleChildNodes.length" class="kg-node-chip-list">
                    <button
                      v-for="child in visibleChildNodes"
                      :key="child.id"
                      class="kg-node-chip"
                      @click="focusNodeFromSidebar(child.id)"
                    >{{ formatNodeLabel(child) }}</button>
                  </div>
                  <div v-else class="kg-empty-hint">当前节点没有子节点。</div>
                  <div v-if="hiddenChildNodeCount" class="kg-inline-tip">其余 {{ hiddenChildNodeCount }} 个子节点可继续在图谱中展开查看。</div>
                </div>

                <div class="kg-panel-section kg-source-preview-section">
                  <div class="kg-section-heading">
                    <div class="kg-depth-label">原文出处</div>
                    <button class="kg-text-link" @click="openTextView('source')">全文视图</button>
                  </div>
                  <div v-if="activeSourceHtml" class="kg-source-preview" v-html="activeSourceHtml"></div>
                  <div v-else class="kg-empty-hint">当前节点暂时没有可定位的原文映射。</div>
                </div>
              </div>
            </template>
          </div>
        </div>
        <div v-show="activeView === 'text'" class="graph-text">
          <div class="kg-text-toolbar">
            <div class="kg-text-view-switch">
              <button class="kg-text-mode-btn" :class="{ active: textMode === 'graph' }" @click="textMode = 'graph'">知识图谱式简化版</button>
              <button class="kg-text-mode-btn" :class="{ active: textMode === 'source' }" :disabled="!hasSourceStructureTree" @click="openTextView('source')">原文结构化版</button>
            </div>
            <div class="kg-text-caption">{{ textModeDescription }}</div>
          </div>
          <div v-if="activeTextTree.length" class="tree-list tree-list-rich">
            <GraphTextNode
              v-for="node in activeTextTree"
              :key="node.id"
              :node="node"
              :active-node-id="activeNodeId || ''"
              :depth-color="depthColor"
            />
          </div>
          <div v-else class="tree-empty-shell">
            <div class="tree-empty-copy">{{ activeTextEmptyCopy }}</div>
            <div class="tree-empty" v-html="highlightedText"></div>
          </div>
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
import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import * as echarts from 'echarts/core';
import { GraphChart } from 'echarts/charts';
import { TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

echarts.use([GraphChart, TooltipComponent, CanvasRenderer]);

const emit = defineEmits(['rewrite']);

const props = defineProps({
  content: { type: String, default: '' },
  nodes: { type: Array, default: () => [] },
  links: { type: Array, default: () => [] },
  dynamicPayload: { type: Object, default: () => ({}) },
  analysisPayload: { type: Object, default: () => ({}) },
  visualConfig: { type: Object, default: () => ({}) },
  originalFileUrl: { type: String, default: '' },
  rewriteTargets: { type: Array, default: () => [] },
  rewriteLoading: { type: Boolean, default: false },
  rewriteEnabled: { type: Boolean, default: false },
});

const activeView = ref('2d');
const textMode = ref('graph');
const showJson = ref(false);
const activeNodeId = ref(null);
const highlightedNodeId = ref(null);
const sidePanelMode = ref('query');
const panelRef = ref(null);
const graph2DWrapperRef = ref(null);
const graph2DRef = ref(null);
const graph3DRef = ref(null);
const graphZoom = ref(1);
const searchQuery = ref('');
const filterDepth = ref(null);
const isFullscreen = ref(false);
const graphThemeVersion = ref(0);
const selectedGlowState = ref({
  visible: false,
  left: 0,
  top: 0,
  size: 0,
  core: 'rgba(255, 255, 255, 0.88)',
  halo: 'rgba(255, 255, 255, 0.28)',
  accent: 'rgba(255, 255, 255, 0.18)',
});

let chart2D = null;
let themeObserver = null;
let resizeObserver = null;
let animationFrame = null;
let clusterFollowFrame = null;
let selectedGlowFrame = null;
let isSyncingOverlayRoam = false;

const SOURCE_STRUCTURE_NODE_TYPES = new Set(['结构', '章节', '段落', '条目', '句子']);
const CLUSTER_CHILD_THRESHOLD = 30;
const CLUSTER_MIN_DOMINANT_TYPE_RATIO = 0.68;
const CLUSTER_MIN_LEAF_RATIO = 0.62;
const CLUSTER_MAX_AVG_LABEL = 18;
const MAIN_GRAPH_SERIES_ID = 'kg_main_graph';
const CLUSTER_OVERLAY_SERIES_ID = 'kg_cluster_overlay';
const GRAPH_DEFAULT_CENTER = ['50%', '50%'];
const SOURCE_CONTEXT_RADIUS = 180;
const MAX_RELATION_CHIPS = 24;
const FILTER_FADE_OPACITY = 0.06;
const FILTER_EDGE_FADE_OPACITY = 0.025;

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

const readCssVar = (name, fallback = '') => {
  if (typeof window === 'undefined' || !document?.documentElement) return fallback;
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
};

const parseColor = (value, fallback = [192, 57, 43]) => {
  const raw = String(value || '').trim();
  if (!raw) return [...fallback];
  const hex = raw.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (hex) {
    const valueText = hex[1];
    const normalized = valueText.length === 3
      ? valueText.split('').map((char) => `${char}${char}`).join('')
      : valueText;
    return [
      parseInt(normalized.slice(0, 2), 16),
      parseInt(normalized.slice(2, 4), 16),
      parseInt(normalized.slice(4, 6), 16),
    ];
  }
  const rgb = raw.match(/^rgba?\(([^)]+)\)$/i);
  if (rgb) {
    const values = rgb[1].split(',').map((part) => Number.parseFloat(part.trim()));
    if (values.length >= 3 && values.slice(0, 3).every((item) => Number.isFinite(item)))
      return values.slice(0, 3).map((item) => clamp(Math.round(item), 0, 255));
  }
  return [...fallback];
};

const mixColor = (base, target, ratio = 0.5) => (
  [0, 1, 2].map((index) => Math.round(base[index] + ((target[index] - base[index]) * clamp(ratio, 0, 1))))
);

const colorToHex = (rgb) => `#${rgb.map((channel) => clamp(Math.round(channel), 0, 255).toString(16).padStart(2, '0')).join('')}`;
const colorToRgba = (rgb, alpha = 1) => `rgba(${rgb.map((channel) => clamp(Math.round(channel), 0, 255)).join(', ')}, ${clamp(alpha, 0, 1)})`;

const graphTheme = computed(() => {
  graphThemeVersion.value;
  const primary = parseColor(readCssVar('--color-primary', '#c0392b'));
  const primaryLight = parseColor(readCssVar('--color-primary-light', '#e45846'), primary);
  const primaryDark = parseColor(readCssVar('--color-primary-dark', '#8e231b'), primary);
  const secondary = parseColor(readCssVar('--color-secondary', '#e67e22'), primaryLight);
  const accentCool = parseColor(readCssVar('--color-accent-cool', '#58cbff'), secondary);
  const accentMint = parseColor(readCssVar('--color-accent-mint', '#80fab0'), accentCool);
  const text = parseColor(readCssVar('--text-primary', '#111111'), [17, 17, 17]);
  const textSecondary = parseColor(readCssVar('--text-secondary', '#666666'), [102, 102, 102]);
  const border = parseColor(readCssVar('--border-color', '#e0e0e0'), [224, 224, 224]);
  const surface = parseColor(readCssVar('--card-bg', '#ffffff'), [255, 255, 255]);
  const depthPalette = [
    colorToHex(mixColor(primaryDark, primary, 0.34)),
    colorToHex(primary),
    colorToHex(mixColor(primaryLight, secondary, 0.42)),
    colorToHex(secondary),
    colorToHex(mixColor(secondary, accentCool, 0.56)),
    colorToHex(accentCool),
    colorToHex(mixColor(accentCool, accentMint, 0.55)),
  ];
  const dark = isDark();
  return {
    depthPalette,
    tooltipBackground: dark ? colorToRgba(mixColor(surface, [0, 0, 0], 0.18), 0.94) : colorToRgba(surface, 0.96),
    tooltipBorder: dark ? colorToRgba(border, 0.88) : colorToRgba(mixColor(border, primary, 0.12), 0.9),
    tooltipText: colorToHex(text),
    label: colorToHex(text),
    labelMuted: colorToHex(textSecondary),
    rootBorder: colorToRgba(mixColor(surface, primaryLight, dark ? 0.18 : 0.08), dark ? 0.85 : 0.92),
    highlightBorder: colorToRgba(mixColor(surface, primaryLight, 0.42), 0.96),
    collapsedBorder: colorToRgba(mixColor(surface, primary, dark ? 0.22 : 0.12), dark ? 0.84 : 0.72),
    glow: colorToRgba(mixColor(primary, accentCool, 0.26), dark ? 0.34 : 0.24),
    edgePositive: colorToRgba(mixColor(secondary, accentCool, 0.4), dark ? 0.72 : 0.62),
    edgeNegative: colorToRgba(mixColor(primary, primaryLight, 0.34), dark ? 0.82 : 0.74),
    edgeOverlay: colorToRgba(mixColor(primary, accentCool, 0.32), dark ? 0.7 : 0.56),
    typePalette: {
      主题: colorToHex(primary),
      对象: colorToHex(accentCool),
      流程: colorToHex(mixColor(secondary, accentCool, 0.28)),
      材料: colorToHex(accentMint),
      时间: colorToHex(mixColor(secondary, [255, 255, 255], 0.24)),
      约束: colorToHex(mixColor(primaryDark, accentCool, 0.24)),
      风险: colorToHex(mixColor(primary, [255, 255, 255], dark ? 0.08 : 0.18)),
      实体: colorToHex(mixColor(textSecondary, accentCool, dark ? 0.1 : 0.18)),
      结构: colorToHex(mixColor(border, secondary, 0.22)),
      章节: colorToHex(mixColor(primaryDark, secondary, 0.36)),
      段落: colorToHex(mixColor(secondary, accentMint, 0.26)),
      条目: colorToHex(mixColor(accentCool, accentMint, 0.22)),
      句子: colorToHex(mixColor(textSecondary, border, 0.22)),
    },
  };
});

const depthColor = (depthValue = 0) => {
  const palette = graphTheme.value.depthPalette;
  const normalized = Math.abs(Number(depthValue) || 0);
  return palette[normalized % palette.length];
};

const typeColor = (type) => graphTheme.value.typePalette[type] || depthColor(1);

const selectedGlowStyle = computed(() => ({
  left: `${selectedGlowState.value.left}px`,
  top: `${selectedGlowState.value.top}px`,
  width: `${selectedGlowState.value.size}px`,
  height: `${selectedGlowState.value.size}px`,
  '--kg-gloss-core': selectedGlowState.value.core,
  '--kg-gloss-halo': selectedGlowState.value.halo,
  '--kg-gloss-accent': selectedGlowState.value.accent,
}));

const baseNodes = computed(() =>
  (props.nodes || []).map((item, idx) => ({
    id: String(item?.id || `node_${idx + 1}`),
    label: sanitizeNodeLabel(item?.label, `节点${idx + 1}`),
    type: String(item?.type || '实体'),
    importance: clamp(Number(item?.importance ?? 0.5), 0, 1),
    layer: item?.layer ? String(item.layer) : '',
    group: item?.group ? String(item.group) : '',
    parent_id: item?.parent_id ? String(item.parent_id) : null,
    properties: item?.properties && typeof item.properties === 'object' ? item.properties : {},
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

const rewriteTargetsSafe = computed(() =>
  (Array.isArray(props.rewriteTargets) ? props.rewriteTargets : [])
    .map((item) => String(item || '').trim())
    .filter(Boolean)
);

const selectedNode = computed(() => nodeById.value.get(String(activeNodeId.value || '').trim()) || null);

const selectedNodeDepth = computed(() => {
  if (!selectedNode.value) return null;
  const depthValue = graphHierarchy.value.depth.get(selectedNode.value.id);
  return Number.isFinite(Number(depthValue)) ? Number(depthValue) : null;
});

const selectedParentNode = computed(() => {
  if (!selectedNode.value) return null;
  const parentId = graphHierarchy.value.parent.get(selectedNode.value.id);
  return parentId ? nodeById.value.get(parentId) || null : null;
});

const selectedChildNodes = computed(() => {
  if (!selectedNode.value) return [];
  return (graphHierarchy.value.children.get(selectedNode.value.id) || [])
    .map((id) => nodeById.value.get(id))
    .filter(Boolean);
});

const visibleChildNodes = computed(() => selectedChildNodes.value.slice(0, MAX_RELATION_CHIPS));

const hiddenChildNodeCount = computed(() => Math.max(0, selectedChildNodes.value.length - visibleChildNodes.value.length));

const textMapping = computed(() => {
  const mapping = props.visualConfig?.text_mapping;
  return mapping && typeof mapping === 'object' ? mapping : {};
});

const prettyDynamicPayload = computed(() => JSON.stringify(props.dynamicPayload || {}, null, 2));

const personalRecommendation = computed(() => {
  const raw = props.analysisPayload?.personal_recommendation;
  return raw && typeof raw === 'object' ? raw : null;
});

const recommendationScore = computed(() => clamp(Math.round(Number(personalRecommendation.value?.score || 0)), 0, 100));
const recommendationToneClass = computed(() => `is-${String(personalRecommendation.value?.level || 'low')}`);
const recommendationPriority = computed(() => String(personalRecommendation.value?.priority_label || '').trim());
const recommendationProfileLabel = computed(() => String(personalRecommendation.value?.profile_label || '').trim());
const recommendationSummary = computed(() => String(personalRecommendation.value?.summary || '').trim());
const recommendationKeywords = computed(() =>
  (Array.isArray(personalRecommendation.value?.matched_keywords) ? personalRecommendation.value.matched_keywords : [])
    .map((item) => String(item || '').trim())
    .filter(Boolean)
    .slice(0, 6)
);
const recommendationReasons = computed(() =>
  (Array.isArray(personalRecommendation.value?.reasons) ? personalRecommendation.value.reasons : [])
    .map((item) => String(item || '').trim())
    .filter(Boolean)
    .slice(0, 3)
);
const recommendationSuggestions = computed(() =>
  (Array.isArray(personalRecommendation.value?.suggestions) ? personalRecommendation.value.suggestions : [])
    .map((item) => String(item || '').trim())
    .filter(Boolean)
    .slice(0, 3)
);

const escapeHtml = (value) =>
  String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');

const normalizeTextRange = (range, content = props.content || '') => {
  if (!Array.isArray(range) || range.length < 2) return null;
  const start = Number(range[0]);
  const end = Number(range[1]);
  if (!Number.isFinite(start) || !Number.isFinite(end) || start < 0 || end <= start || end > content.length) return null;
  return { start, end };
};

const highlightedText = computed(() => {
  const content = props.content || '';
  const ranges = Object.entries(textMapping.value).map(([nodeId, range]) => {
    const normalized = normalizeTextRange(range, content);
    return normalized ? { nodeId, ...normalized } : null;
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

  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  subtreeIds.forEach((id) => {
    const point = positions.get(id);
    if (!point) return;
    minX = Math.min(minX, point.x);
    maxX = Math.max(maxX, point.x);
    minY = Math.min(minY, point.y);
    maxY = Math.max(maxY, point.y);
  });

  if (
    Number.isFinite(minX)
    && Number.isFinite(maxX)
    && Number.isFinite(minY)
    && Number.isFinite(maxY)
  ) {
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    if (Math.abs(centerX) > 0.5 || Math.abs(centerY) > 0.5) {
      subtreeIds.forEach((id) => {
        const point = positions.get(id);
        if (!point) return;
        positions.set(id, {
          x: point.x - centerX,
          y: point.y - centerY,
        });
      });
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
  clearSimpleNodeEmphasis();
  highlightedNodeId.value = null;
  sidePanelMode.value = 'query';
  filterDepth.value = filterDepth.value === d ? null : d;
  stopSelectedGlowSync();
  hideSelectedGlow();
  nextTick(() => { render2DGraph(); });
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

const getNodeTextRange = (nodeId) => {
  const id = String(nodeId || '').trim();
  const mapped = normalizeTextRange(textMapping.value?.[id]);
  if (mapped) return mapped;
  const node = nodeById.value.get(id);
  return normalizeTextRange(node?.properties?.span || node?.properties?.source_span || node?.properties?.text_span);
};

const resolveSourceMatch = (nodeId) => {
  const direct = getNodeTextRange(nodeId);
  if (direct) return { matchNodeId: nodeId, relation: 'self', ...direct };

  const descendants = [...(graphHierarchy.value.children.get(nodeId) || [])];
  const seen = new Set(descendants);
  while (descendants.length) {
    const current = descendants.shift();
    const mapped = getNodeTextRange(current);
    if (mapped) return { matchNodeId: current, relation: 'child', ...mapped };
    for (const child of (graphHierarchy.value.children.get(current) || [])) {
      if (seen.has(child)) continue;
      seen.add(child);
      descendants.push(child);
    }
  }

  let currentParent = graphHierarchy.value.parent.get(nodeId);
  const parentSeen = new Set();
  while (currentParent && !parentSeen.has(currentParent)) {
    parentSeen.add(currentParent);
    const mapped = getNodeTextRange(currentParent);
    if (mapped) return { matchNodeId: currentParent, relation: 'parent', ...mapped };
    currentParent = graphHierarchy.value.parent.get(currentParent);
  }
  return null;
};

const activeSourceMatch = computed(() => {
  if (!selectedNode.value) return null;
  return resolveSourceMatch(selectedNode.value.id);
});

const activeSourceMatchNode = computed(() => {
  if (!activeSourceMatch.value?.matchNodeId) return null;
  return nodeById.value.get(activeSourceMatch.value.matchNodeId) || null;
});

const activeSourceNodeTitle = computed(() => {
  if (!selectedNode.value) return '未选中节点';
  return formatNodeLabel(selectedNode.value) || '未命名节点';
});

const activeSourceNotice = computed(() => {
  if (!selectedNode.value) return '点击图谱中的节点后，这里会展示原文出处。';
  if (!activeSourceMatch.value) return '当前节点暂无直接原文映射，可以继续查看父子节点定位相关出处。';
  if (activeSourceMatch.value.relation === 'self') return '已定位到该节点对应的原文出处。';
  const matchLabel = activeSourceMatchNode.value ? `“${formatNodeLabel(activeSourceMatchNode.value)}”` : '关联节点';
  if (activeSourceMatch.value.relation === 'child') return `当前节点暂无直接映射，已定位到子节点 ${matchLabel} 的原文出处。`;
  return `当前节点暂无直接映射，已定位到父节点 ${matchLabel} 的原文出处。`;
});

const activeSourceHtml = computed(() => {
  const content = props.content || '';
  const match = activeSourceMatch.value;
  if (!content || !match) return '';
  const prefixStart = Math.max(0, match.start - SOURCE_CONTEXT_RADIUS);
  const suffixEnd = Math.min(content.length, match.end + SOURCE_CONTEXT_RADIUS);
  const prefix = prefixStart > 0 ? '…' : '';
  const suffix = suffixEnd < content.length ? '…' : '';
  return `${prefix}${escapeHtml(content.slice(prefixStart, match.start))}<mark class="kg-source-highlight">${escapeHtml(content.slice(match.start, match.end))}</mark>${escapeHtml(content.slice(match.end, suffixEnd))}${suffix}`;
});

const isSourceStructureNode = (node) => {
  if (!node) return false;
  const label = String(node.label || '').trim();
  const type = String(node.type || '').trim();
  return label === '原文结构' || SOURCE_STRUCTURE_NODE_TYPES.has(type) || node.properties?.source === 'original_text';
};

const sourceStructureRootId = computed(() => {
  const exact = safeNodes.value.find((node) => String(node.label || '').trim() === '原文结构' && node.properties?.source === 'original_text');
  if (exact?.id) return exact.id;
  const rootId = rootNodeId.value;
  return (graphHierarchy.value.children.get(rootId) || [])
    .map((id) => nodeById.value.get(id))
    .find((node) => node && isSourceStructureNode(node))?.id || null;
});

const sourceStructureNodeIds = computed(() => {
  const ids = new Set();
  if (!sourceStructureRootId.value) return ids;
  ids.add(sourceStructureRootId.value);
  for (const nodeId of collectDescendants(sourceStructureRootId.value, graphHierarchy.value.children)) ids.add(nodeId);
  return ids;
});

const TEXT_WRAPPER_KEYS = new Set(['content', 'children', 'items', 'payload', 'dynamicpayload', 'dynamic_payload', 'data', 'text', 'result', 'value']);
const TEXT_CONTENT_KEYS = ['title', 'heading', 'name', 'label', 'content', 'text', 'value', 'summary', 'desc', 'description', 'body'];

const normalizeWrapperToken = (value) => String(value || '')
  .toLowerCase()
  .replace(/[\s"'`{}\[\]():：,]/g, '');

const isGenericTextWrapper = (value) => {
  const token = normalizeWrapperToken(value);
  return TEXT_WRAPPER_KEYS.has(token) || token === 'contentroot' || token === 'rootcontent';
};

const decodeEscapedDisplayText = (value) => String(value ?? '')
  .replace(/\\r\\n|\\n\\r|\\r/g, '\n')
  .replace(/\\n/g, '\n')
  .replace(/\\t/g, '  ')
  .replace(/\\"/g, '"')
  .replace(/\\\\/g, '\\');

const tryParseJsonLabel = (value) => {
  const raw = String(value || '').trim();
  if (!raw || !/^[\[{]/.test(raw)) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

const extractDisplayTextFromUnknown = (value, depth = 0) => {
  if (depth > 5 || value === null || value === undefined) return '';
  if (typeof value === 'string') {
    const decoded = decodeEscapedDisplayText(value).trim();
    if (!decoded) return '';
    const nested = tryParseJsonLabel(decoded);
    if (nested && nested !== value) {
      const nestedText = extractDisplayTextFromUnknown(nested, depth + 1);
      if (nestedText) return nestedText;
    }
    return decoded;
  }
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) {
    return value
      .map((item) => extractDisplayTextFromUnknown(item, depth + 1))
      .filter(Boolean)
      .join('\n');
  }
  if (typeof value === 'object') {
    for (const key of TEXT_CONTENT_KEYS) {
      if (!(key in value)) continue;
      const hit = extractDisplayTextFromUnknown(value[key], depth + 1);
      if (hit) return hit;
    }
    for (const [key, nestedValue] of Object.entries(value)) {
      if (!TEXT_WRAPPER_KEYS.has(normalizeWrapperToken(key))) continue;
      const hit = extractDisplayTextFromUnknown(nestedValue, depth + 1);
      if (hit) return hit;
    }
    const scalarLines = Object.entries(value)
      .map(([key, nestedValue]) => {
        if (nestedValue === null || nestedValue === undefined) return '';
        if (typeof nestedValue === 'object') return '';
        const text = extractDisplayTextFromUnknown(nestedValue, depth + 1);
        if (!text) return '';
        return `${key}: ${text}`;
      })
      .filter(Boolean);
    return scalarLines.join('\n');
  }
  return '';
};

const cleanTextTreeLabel = (value) => {
  const raw = String(value || '').trim();
  if (!raw) return '';
  if (isGenericTextWrapper(raw)) return '';
  const jsonContentKeyOnly = raw.match(/^\{\s*"?(content|data|payload|text)"?\s*\}$/i);
  if (jsonContentKeyOnly) return '';
  const wrappedKeyOnly = raw.match(/^[\[{(]\s*"?(content|data|payload|text)"?\s*[\]})]$/i);
  if (wrappedKeyOnly) return '';
  const parsed = tryParseJsonLabel(raw);
  if (parsed) {
    const extracted = extractDisplayTextFromUnknown(parsed);
    if (extracted) return extracted;
  }
  return decodeEscapedDisplayText(raw);
};

const buildTextTree = (rootIds = [], options = {}) => {
  const visit = (nodeId, depth = 1, visited = new Set()) => {
    const id = String(nodeId || '').trim();
    if (!id || visited.has(id)) return [];
    const node = nodeById.value.get(id);
    if (!node) return [];
    if (typeof options.filter === 'function' && !options.filter(node)) return [];
    const nextVisited = new Set(visited);
    nextVisited.add(id);
    const childIds = graphHierarchy.value.children.get(id) || [];
    const buildChildren = (childDepth) => childIds.flatMap((childId) => visit(childId, childDepth, nextVisited));
    const label = cleanTextTreeLabel(node.label);
    if (options.flattenGenericWrappers && !label && childIds.length) {
      return buildChildren(depth);
    }
    return [{
      id,
      depth,
      label: label || node.label || '未命名节点',
      children: buildChildren(depth + 1),
    }];
  };
  return rootIds.flatMap((nodeId) => visit(nodeId, 1));
};

const buildContentFallbackTree = (content = '') => {
  const raw = decodeEscapedDisplayText(String(content || '')).replace(/\r/g, '').trim();
  if (!raw) return [];
  const blocks = raw
    .split(/\n\s*\n+/)
    .map((block) => block.split('\n').map((line) => line.trim()).filter(Boolean))
    .filter((lines) => lines.length);
  return blocks.map((lines, index) => {
    const headingLike = /^(第[一二三四五六七八九十百千万0-9]+[章节条款]|[一二三四五六七八九十0-9]+[、.．）)])/.test(lines[0]);
    const children = lines.length > 1
      ? lines.slice(headingLike ? 1 : 0).map((line, childIndex) => ({
          id: `source_fallback_${index + 1}_${childIndex + 1}`,
          depth: headingLike ? 2 : 2,
          label: line,
          children: [],
        }))
      : [];
    return {
      id: `source_fallback_${index + 1}`,
      depth: 1,
      label: headingLike ? lines[0] : shorten(lines.join(' / '), 160),
      children,
    };
  });
};

const simplifiedTextTree = computed(() => {
  const rootId = rootNodeId.value;
  if (!rootId) return [];
  const rootIds = (graphHierarchy.value.children.get(rootId) || [])
    .filter((nodeId) => !sourceStructureNodeIds.value.has(nodeId));
  return buildTextTree(rootIds, { flattenGenericWrappers: true });
});

const sourceStructuredTextTree = computed(() => {
  if (sourceStructureRootId.value) {
    const sourceTree = buildTextTree(graphHierarchy.value.children.get(sourceStructureRootId.value) || [], { flattenGenericWrappers: true });
    if (sourceTree.length) return sourceTree;
  }
  return buildContentFallbackTree(props.content);
});

const hasSourceStructureTree = computed(() => sourceStructuredTextTree.value.length > 0);

const activeTextTree = computed(() => (textMode.value === 'source' ? sourceStructuredTextTree.value : simplifiedTextTree.value));

const textModeDescription = computed(() => {
  if (textMode.value === 'source') return hasSourceStructureTree.value ? '按原文章节、段落和句群完整展开。' : '当前结果没有可用的原文结构节点。';
  return '剥离原文结构节点后，保留语义关系树，适合快速通读。';
});

const activeTextEmptyCopy = computed(() => (
  textMode.value === 'source'
    ? '当前结果没有可用的原文结构节点，以下回退展示原文高亮全文。'
    : hasSourceStructureTree.value
      ? '当前结果没有可展开的语义节点树，可切换到“原文结构化版”继续查看。'
      : '当前结果没有可展开的语义节点树，以下回退展示原文高亮全文。'
));

const openTextView = (mode = 'graph') => {
  if (mode === 'source') {
    textMode.value = hasSourceStructureTree.value ? 'source' : 'graph';
  } else {
    textMode.value = 'graph';
  }
  activeView.value = 'text';
};

const syncFullscreenState = () => {
  const fullscreenElement = document.fullscreenElement;
  isFullscreen.value = !!(fullscreenElement && panelRef.value && (fullscreenElement === panelRef.value || panelRef.value.contains(fullscreenElement)));
  nextTick(() => {
    chart2D?.resize();
    resizeThreeRenderer();
  });
};

const toggleFullscreen = async () => {
  if (!panelRef.value || typeof panelRef.value.requestFullscreen !== 'function') return;
  try {
    if (document.fullscreenElement && isFullscreen.value && document.exitFullscreen) {
      await document.exitFullscreen();
    } else if (!document.fullscreenElement) {
      await panelRef.value.requestFullscreen();
    }
  } catch (_) {
    nextTick(() => {
      chart2D?.resize();
      resizeThreeRenderer();
    });
  }
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

const switchToQueryPanel = () => {
  sidePanelMode.value = 'query';
};

const triggerRewrite = (target) => {
  const nextTarget = String(target || '').trim();
  if (!nextTarget || !props.rewriteEnabled || props.rewriteLoading) return;
  emit('rewrite', nextTarget);
};

const focusNodeById = (nodeId, options = {}) => {
  const id = String(nodeId || '').trim();
  if (!id || !nodeById.value.has(id)) return false;
  const prevHighlightedId = highlightedNodeId.value;
  const hadQueryFilters = !!searchQuery.value || filterDepth.value !== null;
  activeNodeId.value = id;
  highlightedNodeId.value = id;
  searchQuery.value = '';
  filterDepth.value = null;
  sidePanelMode.value = 'source';
  if (activeView.value !== '2d') return true;
  const shouldRender = !!options.forceRender || hadQueryFilters || !findSeriesNodeRefsById(id).length;
  if (shouldRender) {
    nextTick(() => { render2DGraph(); });
  } else {
    applySimpleNodeEmphasis(id, prevHighlightedId);
    applyHighlightOverlay();
    startSelectedGlowSync();
  }
  return true;
};

const focusNodeFromSidebar = (nodeId) => {
  focusNodeById(nodeId, { forceRender: true });
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

const hideSelectedGlow = () => {
  selectedGlowState.value = {
    ...selectedGlowState.value,
    visible: false,
  };
};

const stopSelectedGlowSync = () => {
  if (!selectedGlowFrame) return;
  cancelAnimationFrame(selectedGlowFrame);
  selectedGlowFrame = null;
};

const buildHighlightContext = () => {
  const query = searchQuery.value.trim().toLowerCase();
  const hasQuery = !!query;
  const hasDepthFilter = filterDepth.value !== null;
  const focusId = String(highlightedNodeId.value || '').trim();
  const descendants = focusId ? getDescendants(focusId) : null;
  const matchedNodeIds = new Set();

  if (hasQuery || hasDepthFilter) {
    safeNodes.value.forEach((node) => {
      const id = String(node?.id || '').trim();
      if (!id) return;
      const matchesSearch = hasQuery && String(node?.label || '').toLowerCase().includes(query);
      const matchesDepth = hasDepthFilter && Number(depthMapCache.value.get(id) ?? 0) === filterDepth.value;
      if (matchesSearch || matchesDepth) matchedNodeIds.add(id);
    });
  }

  return {
    query,
    hasQuery,
    hasDepthFilter,
    hasFilters: hasQuery || hasDepthFilter,
    focusId,
    descendants,
    matchedNodeIds,
  };
};

const syncSelectedNodeGlow = () => {
  if (!chart2D || activeView.value !== '2d' || !graph2DRef.value || !graph2DWrapperRef.value) {
    hideSelectedGlow();
    return;
  }
  const nodeId = String(highlightedNodeId.value || '').trim();
  if (!nodeId) {
    hideSelectedGlow();
    return;
  }

  const option = chart2D.getOption?.();
  const seriesList = Array.isArray(option?.series) ? option.series : [];
  const graphRect = graph2DRef.value.getBoundingClientRect();
  const wrapperRect = graph2DWrapperRef.value.getBoundingClientRect();

  for (const { seriesIndex, dataIndex } of findSeriesNodeRefsById(nodeId)) {
    const runtime = getGraphRuntime(seriesIndex);
    const graphNode = runtime.graph?.getNodeById?.(nodeId);
    if (!graphNode) continue;

    const point = toXY(graphNode.getLayout());
    const pixel = chart2D.convertToPixel?.({ seriesIndex }, [point.x, point.y]);
    if (!Array.isArray(pixel) || pixel.length < 2 || !pixel.every((value) => Number.isFinite(Number(value)))) continue;

    const renderedItem = seriesList[seriesIndex]?.data?.[dataIndex] || {};
    const baseSize = clamp(Number(renderedItem?.symbolSize || 28), 18, 120);
    const fillColor = renderedItem?.itemStyle?.color || depthColor(Number(depthMapCache.value.get(nodeId) ?? 0));
    const fillRgb = parseColor(fillColor, parseColor(readCssVar('--color-primary', '#c0392b')));
    const haloRgb = mixColor(fillRgb, [255, 255, 255], isDark() ? 0.18 : 0.26);
    const coreRgb = mixColor(fillRgb, [255, 255, 255], 0.48);

    selectedGlowState.value = {
      visible: true,
      left: graphRect.left - wrapperRect.left + Number(pixel[0]),
      top: graphRect.top - wrapperRect.top + Number(pixel[1]),
      size: baseSize * 1.95,
      core: colorToRgba(coreRgb, isDark() ? 0.84 : 0.74),
      halo: colorToRgba(haloRgb, isDark() ? 0.54 : 0.42),
      accent: colorToRgba(fillRgb, isDark() ? 0.46 : 0.34),
    };
    return;
  }

  hideSelectedGlow();
};

const startSelectedGlowSync = () => {
  stopSelectedGlowSync();
  if (activeView.value !== '2d' || !highlightedNodeId.value) {
    hideSelectedGlow();
    return;
  }
  const tick = () => {
    selectedGlowFrame = requestAnimationFrame(tick);
    syncSelectedNodeGlow();
  };
  tick();
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
  const theme = graphTheme.value;
  const fillColor = depthColor(depthValue);
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
    value: clusterCount ? `${node.type} · ${clusterCount} 个子节点` : node.type,
    clusterCount,
    x: point.x,
    y: point.y,
    fixed,
    ignoreForceRepulsion,
    draggable,
    isOverlayNode,
    symbolSize,
    itemStyle: {
      color: fillColor,
      opacity: 1,
      borderWidth: isRoot ? 2.5 : isCollapsedCluster ? 2.2 : 1.1,
      borderColor: isCollapsedCluster ? theme.collapsedBorder : isRoot ? theme.rootBorder : colorToRgba(parseColor(fillColor), dark ? 0.16 : 0.12),
      shadowBlur: isCollapsedCluster ? 24 : isRoot ? 18 : 10,
      shadowColor: isCollapsedCluster ? theme.glow : colorToRgba(parseColor(fillColor), dark ? 0.28 : 0.14),
    },
    label: {
      show: shouldShowNodeLabel(node),
      color: theme.label,
      fontSize: isRoot ? 13 : isOverlayNode ? 10 : 11,
      fontWeight: isRoot ? 700 : 400,
      formatter: () => shorten(isRoot ? documentTitle.value : formatNodeLabel(node), isRoot ? 38 : isOverlayNode ? 18 : 24),
    },
  };
};

const buildEdgeItem = (link, source = link.source, target = link.target, options = {}) => {
  const {
    ignoreForceLayout = false,
    widthScale = 1,
    opacity = 0.85,
    tone = 'main',
  } = options;
  const theme = graphTheme.value;
  return {
    source,
    target,
    value: link.relation,
    ignoreForceLayout,
    lineStyle: {
      color: link.logic_type === 'negative' ? theme.edgeNegative : tone === 'overlay' ? theme.edgeOverlay : theme.edgePositive,
      type: link.logic_type === 'negative' ? 'dashed' : 'solid',
      width: (0.7 + clamp(Number(link.strength || 0.6), 0, 1) * 2.2) * widthScale,
      opacity,
    },
    label: {
      show: shouldShowEdgeLabel(link),
      formatter: () => shorten(link.relation, 10),
      color: theme.labelMuted,
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
    const rootPoint = liveRootPoint;
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

const getCurrentGraphRoamState = () => {
  const fallback = {
    center: [...GRAPH_DEFAULT_CENTER],
    zoom: clamp(Number(graphZoom.value || 1), 0.2, 2.8),
  };
  if (!chart2D) return fallback;
  const option = chart2D.getOption?.();
  const series = (Array.isArray(option?.series) ? option.series : []).find((item) => item?.id === MAIN_GRAPH_SERIES_ID);
  if (!series) return fallback;
  const center = Array.isArray(series.center) && series.center.length >= 2
    ? [series.center[0], series.center[1]]
    : fallback.center;
  const zoom = clamp(Number(series.zoom || fallback.zoom), 0.2, 2.8);
  return { center, zoom };
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

const decorateDisplayedNode = (item, livePositions, dark, context) => {
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
  const theme = graphTheme.value;
  const matchesFilter = context.matchedNodeIds.has(id);

  let color = baseCol;
  let opacity = 1;
  let borderWidth = isCollapsedCluster ? 3 : 1.1;
  let borderColor = isCollapsedCluster ? theme.collapsedBorder : colorToRgba(parseColor(baseCol), dark ? 0.16 : 0.12);
  let labelShow = shouldShowNodeLabel(src || { id, importance: 0.5 });
  let shadowBlur = Number(item?.itemStyle?.shadowBlur ?? (isCollapsedCluster ? 24 : isRoot ? 18 : 10));
  let shadowColor = item?.itemStyle?.shadowColor || (isCollapsedCluster ? theme.glow : colorToRgba(parseColor(baseCol), dark ? 0.28 : 0.14));
  let symbolSize = Number(item?.symbolSize || 0) || undefined;

  if (context.focusId) {
    if (id === context.focusId) {
      color = baseCol;
      borderWidth = 4.4;
      borderColor = theme.highlightBorder;
      opacity = 1;
      shadowBlur = 28;
      shadowColor = theme.glow;
      symbolSize = Math.max(symbolSize || 0, (Number(item?.symbolSize || 0) || 0) * 1.08);
    } else if (context.descendants?.has(id)) {
      opacity = 0.88;
      shadowBlur = Math.max(12, shadowBlur);
    } else {
      opacity = 0.09;
      labelShow = false;
      shadowBlur = 0;
    }
  } else if (matchesFilter) {
    borderWidth = 3.4;
    borderColor = theme.highlightBorder;
    opacity = 1;
    shadowBlur = 20;
    shadowColor = theme.glow;
    symbolSize = Math.max(symbolSize || 0, (Number(item?.symbolSize || 0) || 0) * 1.05);
  } else if (context.hasFilters) {
    opacity = FILTER_FADE_OPACITY;
    labelShow = false;
    shadowBlur = 0;
    borderWidth = Math.max(0.7, borderWidth * 0.6);
    borderColor = colorToRgba(parseColor(baseCol), dark ? 0.06 : 0.05);
  }

  return {
    ...item,
    x: point?.x ?? item.x,
    y: point?.y ?? item.y,
    name: isRoot ? documentTitle.value : formatNodeLabel(src || item),
    ...(symbolSize ? { symbolSize } : {}),
    itemStyle: { ...(item.itemStyle || {}), color, opacity, borderWidth, borderColor, shadowBlur, shadowColor },
    label: {
      ...item.label,
      show: labelShow,
      color: theme.label,
      fontSize: isRoot ? 14 : item?.isOverlayNode ? 10 : 12,
      fontWeight: isRoot ? 700 : 400,
    },
  };
};

const decorateDisplayedEdge = (item, context) => {
  const sourceId = String(item?.source || '');
  const targetId = String(item?.target || '');
  const lineStyle = { ...(item?.lineStyle || {}) };
  let opacity = Number(lineStyle.opacity ?? 0.85);
  let width = Number(lineStyle.width ?? 1);

  if (context.focusId) {
    const sourceVisible = sourceId === context.focusId || context.descendants?.has(sourceId);
    const targetVisible = targetId === context.focusId || context.descendants?.has(targetId);
    if (sourceVisible && targetVisible) {
      opacity = Math.max(opacity, 0.66);
      width *= 1.04;
    } else {
      opacity = 0.04;
    }
  } else if (context.hasFilters) {
    const sourceMatched = context.matchedNodeIds.has(sourceId);
    const targetMatched = context.matchedNodeIds.has(targetId);
    if (sourceMatched || targetMatched) {
      opacity = Math.max(opacity * 0.6, 0.18);
      width *= sourceMatched && targetMatched ? 1.08 : 0.9;
    } else {
      opacity = FILTER_EDGE_FADE_OPACITY;
    }
  }

  return {
    ...item,
    lineStyle: {
      ...lineStyle,
      opacity,
      width,
    },
    label: {
      ...(item?.label || {}),
      show: context.focusId ? false : (!context.hasFilters && !!item?.label?.show),
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
  const context = buildHighlightContext();
  const nextSeries = [];
  const mainSeries = seriesList.find((series) => series?.id === MAIN_GRAPH_SERIES_ID);
  if (mainSeries?.data) {
    const livePositions = readLiveNodePositions(MAIN_GRAPH_SERIES_ID);
    nextSeries.push({
      id: MAIN_GRAPH_SERIES_ID,
      data: mainSeries.data.map((item) => decorateDisplayedNode(item, livePositions, dark, context)),
      links: (Array.isArray(mainSeries.links) ? mainSeries.links : []).map((item) => decorateDisplayedEdge(item, context)),
    });
  }
  const overlaySeries = seriesList.find((series) => series?.id === CLUSTER_OVERLAY_SERIES_ID);
  if (overlaySeries?.data) {
    const livePositions = readLiveNodePositions(CLUSTER_OVERLAY_SERIES_ID);
    nextSeries.push({
      id: CLUSTER_OVERLAY_SERIES_ID,
      data: overlaySeries.data.map((item) => decorateDisplayedNode(item, livePositions, dark, context)),
      links: (Array.isArray(overlaySeries.links) ? overlaySeries.links : []).map((item) => decorateDisplayedEdge(item, context)),
    });
  }
  if (nextSeries.length) chart2D.setOption({ series: nextSeries });
};

const onSearch = () => {
  clearSimpleNodeEmphasis();
  highlightedNodeId.value = null;
  filterDepth.value = null;
  sidePanelMode.value = 'query';
  stopSelectedGlowSync();
  hideSelectedGlow();
  nextTick(() => { render2DGraph(); });
};

const clearHighlight = () => {
  const hadSearchOrDepth = !!searchQuery.value || filterDepth.value !== null;
  clearSimpleNodeEmphasis();
  highlightedNodeId.value = null;
  searchQuery.value = '';
  filterDepth.value = null;
  sidePanelMode.value = 'query';
  stopSelectedGlowSync();
  hideSelectedGlow();
  if (hadSearchOrDepth) nextTick(() => { render2DGraph(); });
};

const render2DGraph = () => {
  if (!graph2DRef.value) return;
  stopClusterFollowerSync();
  stopSelectedGlowSync();
  hideSelectedGlow();
  const preservedRoam = getCurrentGraphRoamState();
  if (!chart2D) chart2D = echarts.init(graph2DRef.value);
  else chart2D.clear();
  graphZoom.value = preservedRoam.zoom;
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
    const displayedOffsetCenter = childIds.reduce((acc, nodeId) => {
      const point = toXY(layout.get(nodeId));
      acc.x += point.x;
      acc.y += point.y;
      return acc;
    }, { x: 0, y: 0 });
    displayedOffsetCenter.x /= childIds.length;
    displayedOffsetCenter.y /= childIds.length;
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
      const rawOffset = toXY(layout.get(nodeId));
      const offset = {
        x: rawOffset.x - displayedOffsetCenter.x,
        y: rawOffset.y - displayedOffsetCenter.y,
      };
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
      overlayEdgeData.push(buildEdgeItem(link, sourceId, targetId, { widthScale: 0.88, opacity: 0.78, tone: 'overlay' }));
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

    followerStates.set(clusterId, {
      anchorId,
      offsets,
      edges: edgeRefs,
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
    const theme = graphTheme.value;
    const fillColor = depthColor(d);
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
        color: fillColor,
        opacity: 1,
        borderWidth: isRoot ? 2.6 : isCollapsedCluster ? 2.2 : 1.1,
        borderColor: isCollapsedCluster ? theme.collapsedBorder : isRoot ? theme.rootBorder : colorToRgba(parseColor(fillColor), dark ? 0.16 : 0.12),
        shadowBlur: isCollapsedCluster ? 24 : isRoot ? 18 : 10,
        shadowColor: isCollapsedCluster ? theme.glow : colorToRgba(parseColor(fillColor), dark ? 0.28 : 0.14),
      },
      label: {
        show: shouldShowNodeLabel(node),
        color: theme.label,
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
      color: link.logic_type === 'negative' ? graphTheme.value.edgeNegative : graphTheme.value.edgePositive,
      type: link.logic_type === 'negative' ? 'dashed' : 'solid',
      width: 0.7 + clamp(Number(link.strength || 0.6), 0, 1) * 2.2,
      opacity: 0.85,
    },
    label: { show: shouldShowEdgeLabel(link), formatter: () => shorten(link.relation, 10), color: graphTheme.value.labelMuted, fontSize: 10 },
  }));
  const series = [{
    id: MAIN_GRAPH_SERIES_ID,
    type: 'graph',
    layout: 'force',
    layoutAnimation: true,
    roam: true,
    center: [...preservedRoam.center],
    zoom: preservedRoam.zoom,
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
      center: [...preservedRoam.center],
      zoom: preservedRoam.zoom,
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
      backgroundColor: graphTheme.value.tooltipBackground,
      borderColor: graphTheme.value.tooltipBorder,
      textStyle: { color: graphTheme.value.tooltipText },
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
        focusNodeById(id, { forceRender: true });
        return;
      }
      if (highlightedNodeId.value === id && sidePanelMode.value === 'source') { clearHighlight(); return; }
      focusNodeById(id);
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
    if (isSyncingOverlayRoam) {
      syncSelectedNodeGlow();
      return;
    }
    if (!Number.isFinite(sourceIndex)) {
      syncSelectedNodeGlow();
      return;
    }
    if (sourceIndex === mainSeriesIndex && overlaySeriesIndex >= 0) {
      syncOverlayRoam(params, overlaySeriesIndex);
    } else if (sourceIndex === overlaySeriesIndex && mainSeriesIndex >= 0) {
      syncOverlayRoam(params, mainSeriesIndex);
    }
    syncSelectedNodeGlow();
  });

  applyHighlightOverlay();
  startClusterFollowerSync();
  startSelectedGlowSync();
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
    const lineColor = link.logic_type === 'negative' ? graphTheme.value.edgeNegative : graphTheme.value.edgePositive;
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([source.position.clone(), target.position.clone()]),
      new THREE.LineBasicMaterial({ color: new THREE.Color(lineColor), transparent: true, opacity: 0.75 })
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
    mesh.material.emissive = new THREE.Color(isActive ? graphTheme.value.edgeNegative : '#000000');
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
const GraphTextNode = defineComponent({
  name: 'GraphTextNode',
  props: {
    node: { type: Object, required: true },
    activeNodeId: { type: String, default: '' },
    depthColor: { type: Function, required: true },
  },
  setup(componentProps) {
    return () => {
      const depth = Number(componentProps.node?.depth || 1);
      const tone = componentProps.depthColor(depth);
      const classes = ['tree-node', `depth-${Math.min(depth, 12)}`, { active: componentProps.activeNodeId === componentProps.node?.id }];
      const children = Array.isArray(componentProps.node?.children) ? componentProps.node.children : [];
      const active = componentProps.activeNodeId === componentProps.node?.id;
      const rowStyle = {
        display: 'block',
        background: active ? 'color-mix(in srgb, var(--color-primary) 4%, var(--card-bg))' : 'var(--card-bg)',
        border: `1px solid ${active ? 'color-mix(in srgb, var(--color-primary) 34%, var(--border-color))' : 'var(--border-color)'}`,
        borderLeft: `3px solid ${tone}`,
        borderRadius: '6px',
        padding: '8px 12px',
        color: 'var(--text-primary)',
        boxSizing: 'border-box',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        lineHeight: '1.7',
      };
      const summaryStyle = {
        ...rowStyle,
        cursor: 'pointer',
        fontWeight: 600,
        userSelect: 'none',
        listStyle: 'none',
        margin: 0,
      };
      const childrenStyle = {
        marginTop: '8px',
        paddingLeft: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
      };
      const arrowStyle = {
        display: 'inline-block',
        width: '12px',
        marginRight: '4px',
        fontSize: '10px',
        opacity: 0.6,
      };
      if (children.length) {
        return h('details', { class: classes, open: true }, [
          h('summary', { class: 'tree-summary', style: summaryStyle }, [
            h('span', { style: arrowStyle }, '▼'),
            h('span', componentProps.node.label || '未命名节点'),
          ]),
          h('div', { class: 'tree-children', style: childrenStyle }, children.map((child) => h(GraphTextNode, {
            key: child.id,
            node: child,
            activeNodeId: componentProps.activeNodeId,
            depthColor: componentProps.depthColor,
          }))),
        ]);
      }
      return h('div', { class: [...classes, 'is-leaf'], style: rowStyle }, componentProps.node.label || '未命名节点');
    };
  },
});

// ── watchers & lifecycle ───────────────────────────────────────────────────
watch(
  () => [props.nodes, props.links, props.content, props.visualConfig, props.dynamicPayload],
  () => {
    if (!safeNodes.value.length) {
      sidePanelMode.value = 'query';
      highlightedNodeId.value = null;
      activeNodeId.value = null;
      stopSelectedGlowSync();
      hideSelectedGlow();
      return;
    }
    userExpandedClusterIds.value = new Set([...userExpandedClusterIds.value].filter((id) => clusterMetaMap.value.has(id)));
    graphZoom.value = clamp(Number(props.visualConfig?.initial_zoom ?? 1), 0.2, 2.8);
    if (textMode.value === 'source' && !hasSourceStructureTree.value) textMode.value = 'graph';
    sidePanelMode.value = 'query';
    highlightedNodeId.value = null;
    stopSelectedGlowSync();
    hideSelectedGlow();
    if (!activeNodeId.value || !nodeById.value.has(activeNodeId.value)) {
      activeNodeId.value = props.visualConfig?.focus_node || rootNodeId.value || safeNodes.value[0].id;
    }
    nextTick(() => { render2DGraph(); rebuildThreeGraph(); });
  },
  { immediate: true, deep: true }
);

watch(activeView, (view) => {
  if (view !== '3d') stopThreeAnimation();
  if (view !== '2d') {
    stopClusterFollowerSync();
    stopSelectedGlowSync();
    hideSelectedGlow();
  }
  if (view === '2d') nextTick(() => {
    render2DGraph();
    chart2D?.resize();
    syncSelectedNodeGlow();
  });
  if (view === '3d') nextTick(() => { rebuildThreeGraph(); startThreeAnimation(); });
});

watch(showJson, () => nextTick(() => {
  chart2D?.resize();
  resizeThreeRenderer();
  syncSelectedNodeGlow();
}));

onMounted(() => {
  if (safeNodes.value.length) activeNodeId.value = props.visualConfig?.focus_node || rootNodeId.value || safeNodes.value[0].id;
  sidePanelMode.value = 'query';
  render2DGraph(); rebuildThreeGraph();
  document.addEventListener('fullscreenchange', syncFullscreenState);
  themeObserver = new MutationObserver(() => {
    graphThemeVersion.value += 1;
    render2DGraph();
    refreshThreeStyles();
  });
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'data-color-scheme'] });
  if (graph2DRef.value) {
    resizeObserver = new ResizeObserver(() => {
      chart2D?.resize();
      resizeThreeRenderer();
      syncSelectedNodeGlow();
    });
    resizeObserver.observe(graph2DRef.value);
    if (graph3DRef?.value) resizeObserver.observe(graph3DRef.value);
  }
});

onBeforeUnmount(() => {
  stopThreeAnimation();
  stopClusterFollowerSync();
  stopSelectedGlowSync();
  document.removeEventListener('fullscreenchange', syncFullscreenState);
  threeRenderer?.domElement?.removeEventListener('pointerdown', onThreePointerDown);
  disposeThreeGraph(); threeControls?.dispose?.(); threeRenderer?.dispose?.();
  threeScene = threeCamera = threeControls = threeRenderer = null;
  chart2D?.dispose(); themeObserver?.disconnect(); resizeObserver?.disconnect();
});
</script>

<style scoped>
.kg-panel {
  --kg-panel-border: color-mix(in srgb, var(--color-primary) 12%, var(--border-color));
  --kg-panel-shadow: 0 22px 48px color-mix(in srgb, var(--color-primary) 14%, transparent);
  --kg-card-surface:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 7%, transparent), transparent 42%),
    radial-gradient(circle at 82% 0%, color-mix(in srgb, var(--color-secondary) 10%, transparent), transparent 28%),
    linear-gradient(180deg, color-mix(in srgb, var(--color-primary) 3%, var(--card-bg)), var(--card-bg));
  --kg-graph-surface:
    radial-gradient(circle at 12% 16%, color-mix(in srgb, var(--color-primary) 10%, transparent), transparent 30%),
    radial-gradient(circle at 86% 10%, color-mix(in srgb, var(--color-secondary) 12%, transparent), transparent 24%),
    linear-gradient(180deg, color-mix(in srgb, var(--color-primary) 3%, var(--card-bg)), color-mix(in srgb, var(--color-secondary) 3%, var(--card-bg)));
  --kg-soft-border: color-mix(in srgb, var(--color-primary) 9%, var(--border-color));
  --kg-button-bg: color-mix(in srgb, var(--color-primary) 6%, var(--card-bg));
  --kg-button-bg-hover: color-mix(in srgb, var(--color-primary) 12%, var(--card-bg));
  --kg-button-border: color-mix(in srgb, var(--color-primary) 18%, var(--border-color));
  --kg-button-text: var(--text-primary);
  --kg-button-shadow: 0 10px 18px color-mix(in srgb, var(--color-primary) 10%, transparent);
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 920px;
}

.kg-panel.is-fullscreen {
  min-height: 100vh;
  padding: 14px;
  background: var(--content-bg);
  box-sizing: border-box;
}

.kg-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.kg-tabs,
.kg-actions,
.kg-text-view-switch,
.kg-node-chip-list,
.kg-legend {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.kg-tab,
.kg-tab-disabled,
.kg-toolbar-btn,
.kg-text-mode-btn,
.kg-back-btn,
.kg-rewrite-btn,
.kg-node-chip {
  border: 1px solid var(--kg-button-border);
  background: var(--kg-button-bg);
  color: var(--kg-button-text);
  padding: 7px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease, color 0.18s ease;
  box-shadow: var(--kg-button-shadow);
}

.kg-tab,
.kg-tab-disabled,
.kg-toolbar-btn,
.kg-text-mode-btn,
.kg-back-btn,
.kg-rewrite-btn {
  border-radius: 999px;
}

.kg-node-chip {
  border-radius: 12px;
  text-align: left;
  box-shadow: none;
}

.kg-tab:hover,
.kg-toolbar-btn:hover,
.kg-text-mode-btn:hover:not(:disabled),
.kg-back-btn:hover,
.kg-rewrite-btn:hover:not(:disabled),
.kg-node-chip:hover {
  transform: translateY(-1px);
  background: var(--kg-button-bg-hover);
  border-color: color-mix(in srgb, var(--color-primary) 32%, var(--border-color));
}

.kg-tab.active,
.kg-text-mode-btn.active {
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 58%, var(--color-secondary) 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 14px 26px color-mix(in srgb, var(--color-primary) 22%, transparent);
}

.kg-tab-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.kg-text-mode-btn:disabled,
.kg-toolbar-btn:disabled,
.kg-rewrite-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.kg-meta {
  display: flex;
  gap: 10px;
  color: var(--text-secondary);
  font-size: 12px;
}

.kg-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
  min-height: 840px;
}

.kg-content.json-open { grid-template-columns: minmax(0, 1fr) 360px; }

.kg-main,
.kg-json {
  border: 1px solid var(--kg-panel-border);
  background: var(--kg-card-surface);
  box-shadow: var(--kg-panel-shadow);
  border-radius: 20px;
  overflow: hidden;
}

.kg-main {
  min-height: 840px;
  position: relative;
}

.graph-2d-wrapper {
  position: relative;
  width: 100%;
  height: 840px;
  display: flex;
  background: var(--kg-graph-surface);
}

.graph-2d-wrapper::before,
.graph-2d-wrapper::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.graph-2d-wrapper::before {
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--border-color) 60%, transparent) 1px, transparent 1px),
    linear-gradient(180deg, color-mix(in srgb, var(--border-color) 60%, transparent) 1px, transparent 1px);
  background-size: 26px 26px;
  opacity: 0.14;
}

.graph-2d-wrapper::after {
  background:
    radial-gradient(circle at center, transparent 55%, color-mix(in srgb, var(--color-primary) 10%, transparent) 100%);
  opacity: 0.5;
}

.graph-2d {
  position: relative;
  z-index: 1;
  flex: 1;
  height: 840px;
}

.kg-selected-gloss {
  position: absolute;
  z-index: 2;
  border-radius: 999px;
  pointer-events: none;
  transform: translate(-50%, -50%);
  background:
    radial-gradient(circle at 34% 30%, var(--kg-gloss-core) 0%, rgba(255, 255, 255, 0.18) 24%, rgba(255, 255, 255, 0) 58%),
    radial-gradient(circle at center, var(--kg-gloss-accent) 0%, rgba(255, 255, 255, 0.04) 48%, rgba(255, 255, 255, 0) 74%);
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--kg-gloss-core) 46%, transparent),
    0 0 24px var(--kg-gloss-halo),
    0 0 54px var(--kg-gloss-accent);
  mix-blend-mode: screen;
  isolation: isolate;
  overflow: hidden;
  animation: kgGlossPulse 2.15s ease-in-out infinite;
}

.kg-selected-gloss::before,
.kg-selected-gloss::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
}

.kg-selected-gloss::before {
  background:
    linear-gradient(115deg, transparent 16%, rgba(255, 255, 255, 0.08) 36%, rgba(255, 255, 255, 0.52) 50%, rgba(255, 255, 255, 0.12) 62%, transparent 82%);
  transform: translateX(-135%) rotate(8deg);
  opacity: 0.88;
  animation: kgGlossSweep 2.7s cubic-bezier(0.24, 0.1, 0.22, 1) infinite;
}

.kg-selected-gloss::after {
  inset: 10%;
  border: 1px solid color-mix(in srgb, var(--kg-gloss-core) 72%, transparent);
  box-shadow:
    inset 0 0 16px color-mix(in srgb, var(--kg-gloss-core) 22%, transparent),
    0 0 18px color-mix(in srgb, var(--kg-gloss-halo) 80%, transparent);
  opacity: 0.78;
  animation: kgGlossRing 1.95s ease-in-out infinite;
}

.kg-ops-panel {
  position: relative;
  z-index: 3;
  width: 300px;
  flex-shrink: 0;
  border-left: 1px solid var(--kg-panel-border);
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--card-bg) 92%, transparent), color-mix(in srgb, var(--color-primary) 6%, var(--card-bg)));
  backdrop-filter: blur(16px);
  box-sizing: border-box;
  overflow-y: auto;
}

@keyframes kgGlossPulse {
  0%, 100% {
    transform: translate(-50%, -50%) scale(0.96);
    filter: saturate(1) brightness(1);
  }
  45% {
    transform: translate(-50%, -50%) scale(1.05);
    filter: saturate(1.12) brightness(1.08);
  }
  72% {
    transform: translate(-50%, -50%) scale(1.01);
    filter: saturate(1.08) brightness(1.03);
  }
}

@keyframes kgGlossSweep {
  0% {
    transform: translateX(-135%) rotate(8deg);
    opacity: 0;
  }
  18% {
    opacity: 0.9;
  }
  56% {
    opacity: 0.72;
  }
  100% {
    transform: translateX(135%) rotate(8deg);
    opacity: 0;
  }
}

@keyframes kgGlossRing {
  0%, 100% {
    transform: scale(0.94);
    opacity: 0.38;
  }
  50% {
    transform: scale(1.06);
    opacity: 0.92;
  }
}

.kg-side-kicker {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.kg-search {
  width: 100%;
  padding: 10px 13px;
  border-radius: 999px;
  border: 1px solid var(--kg-button-border);
  font-size: 12px;
  outline: none;
  background: color-mix(in srgb, var(--card-bg) 92%, transparent);
  color: var(--text-primary);
  box-sizing: border-box;
}

.kg-search:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary) 14%, transparent);
}

.kg-depth-filter,
.kg-panel-section,
.kg-source-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kg-source-panel {
  gap: 14px;
  min-height: 0;
}

.kg-section-heading,
.kg-source-header,
.kg-text-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.kg-text-toolbar {
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.kg-text-caption,
.kg-inline-status,
.kg-inline-tip,
.kg-empty-hint,
.kg-depth-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.kg-text-caption,
.kg-inline-tip,
.kg-empty-hint {
  line-height: 1.6;
}

.kg-cluster-tip,
.kg-source-notice {
  border: 1px solid var(--kg-soft-border);
  border-radius: 14px;
  padding: 11px 12px;
  background: color-mix(in srgb, var(--card-bg) 88%, transparent);
}

.kg-cluster-copy {
  font-size: 12px;
  line-height: 1.65;
  color: var(--text-secondary);
}

.kg-persona-panel {
  border: 1px solid color-mix(in srgb, var(--color-primary) 16%, var(--border-color));
  border-radius: 16px;
  padding: 12px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-primary) 6%, var(--card-bg)), color-mix(in srgb, var(--color-secondary) 4%, var(--card-bg)));
  box-shadow: 0 14px 28px color-mix(in srgb, var(--color-primary) 10%, transparent);
}

.kg-persona-panel.is-high,
.kg-persona-panel.is-medium {
  border-color: color-mix(in srgb, var(--color-primary) 26%, var(--border-color));
}

.kg-persona-heading {
  align-items: stretch;
}

.kg-persona-score {
  min-width: 84px;
  border-radius: 14px;
  padding: 10px 9px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: linear-gradient(145deg, var(--color-primary-dark), var(--color-primary), var(--color-secondary));
  color: #fff;
  text-align: center;
  box-shadow: 0 14px 26px color-mix(in srgb, var(--color-primary) 24%, transparent);
}

.kg-persona-score strong {
  font-size: 24px;
  line-height: 1;
}

.kg-persona-score span {
  font-size: 10px;
  line-height: 1.4;
  opacity: 0.92;
}

.kg-persona-meta,
.kg-persona-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.kg-persona-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 9px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, var(--border-color));
  background: color-mix(in srgb, var(--color-primary) 8%, var(--card-bg));
  color: color-mix(in srgb, var(--color-primary-dark) 74%, var(--text-primary));
  font-size: 11px;
  line-height: 1.4;
}

.kg-persona-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kg-persona-list {
  margin: 0;
  padding-left: 18px;
  color: var(--text-primary);
  font-size: 12px;
  line-height: 1.65;
}

.kg-persona-list li + li {
  margin-top: 4px;
}

.kg-persona-list.is-action li::marker {
  color: var(--color-primary);
}

.kg-rewrite-grid { display: flex; flex-wrap: wrap; gap: 8px; }

.kg-source-title,
.tree-summary-title {
  color: var(--text-primary);
  font-weight: 700;
}

.kg-source-title {
  font-size: 15px;
  line-height: 1.55;
}

.kg-source-meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }

.kg-source-pill,
.tree-summary-badge,
.tree-summary-meta,
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  font-size: 11px;
}

.kg-source-pill,
.tree-summary-badge,
.tree-summary-meta {
  padding: 3px 8px;
  border: 1px solid var(--kg-soft-border);
  background: color-mix(in srgb, var(--card-bg) 92%, transparent);
}

.kg-source-pill,
.tree-summary-meta {
  color: var(--text-secondary);
}

.tree-summary-badge {
  color: color-mix(in srgb, var(--color-primary-dark) 76%, var(--text-primary));
  background: color-mix(in srgb, var(--color-primary) 9%, var(--card-bg));
}

.kg-source-link,
.kg-text-link {
  font-size: 12px;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 700;
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
}

.kg-source-link:hover,
.kg-text-link:hover { text-decoration: underline; }

.kg-source-preview {
  min-height: 220px;
  max-height: 420px;
  overflow: auto;
  white-space: pre-wrap;
  line-height: 1.8;
  color: var(--text-primary);
  font-size: 12px;
  border: 1px solid var(--kg-soft-border);
  border-radius: 14px;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
  padding: 12px 14px;
  box-sizing: border-box;
}

.kg-source-preview-section {
  flex: 1;
  min-height: 0;
}

.graph-text {
  width: 100%;
  height: 840px;
  overflow-y: auto;
  padding: 14px;
  box-sizing: border-box;
  background: transparent;
}

.tree-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tree-node {
  font-size: 13px;
  color: var(--text-primary);
  background: transparent;
  border: none;
  padding: 0;
  box-shadow: none;
}

.tree-node.is-leaf {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-left: 3px solid;
  border-radius: 6px;
  padding: 8px 12px;
  font-weight: 500;
}

.tree-summary {
  display: block;
}

.tree-summary::-webkit-details-marker { display: none; }

.tree-node.active > .tree-summary,
.tree-node.is-leaf.active {
  border-color: color-mix(in srgb, var(--color-primary) 34%, var(--border-color));
  background: color-mix(in srgb, var(--color-primary) 4%, var(--card-bg));
}

.tree-children {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 12px;
}

.tree-empty-shell {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tree-empty-copy {
  font-size: 12px;
  color: var(--text-secondary);
}

.tree-empty {
  white-space: pre-wrap;
  line-height: 1.7;
  color: var(--text-primary);
  border: 1px solid color-mix(in srgb, var(--border-color) 92%, var(--color-primary) 8%);
  border-radius: 8px;
  background: var(--card-bg);
  padding: 14px;
}

.kg-json {
  min-height: 840px;
  display: flex;
  flex-direction: column;
}

.kg-json-title {
  padding: 10px 14px;
  font-size: 12px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--kg-soft-border);
  flex-shrink: 0;
}

.kg-json pre {
  margin: 0;
  padding: 12px 14px;
  overflow: auto;
  font-size: 12px;
  color: var(--text-primary);
  flex: 1;
}

.legend-item {
  padding: 4px 10px;
  color: var(--text-secondary);
  border: 1px solid var(--kg-soft-border);
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
}

.legend-dot { width: 9px; height: 9px; border-radius: 50%; }

:deep(.kg-entity) {
  background: color-mix(in srgb, var(--color-secondary) 26%, transparent);
  border-radius: 4px;
  padding: 0 2px;
}

:deep(.kg-entity.active) {
  background: color-mix(in srgb, var(--color-primary) 24%, transparent);
  outline: 1px solid color-mix(in srgb, var(--color-primary) 62%, transparent);
}

:deep(.kg-source-highlight) {
  background: color-mix(in srgb, var(--color-secondary) 24%, transparent);
  border-radius: 4px;
  padding: 0 2px;
}

:global([data-theme="dark"]) .kg-panel {
  --kg-panel-shadow: 0 24px 52px rgba(0, 0, 0, 0.34);
  --kg-button-shadow: 0 12px 22px rgba(0, 0, 0, 0.26);
}

:global([data-theme="dark"]) .graph-2d-wrapper::before { opacity: 0.08; }

:global([data-theme="dark"]) .graph-2d-wrapper::after { opacity: 0.32; }

:global([data-theme="dark"]) .kg-entity {
  background: color-mix(in srgb, var(--color-secondary) 18%, rgba(255, 255, 255, 0.04));
}

:global([data-theme="dark"]) .kg-entity.active {
  background: color-mix(in srgb, var(--color-primary) 20%, rgba(255, 255, 255, 0.05));
}

:global([data-theme="dark"]) .kg-source-highlight {
  background: color-mix(in srgb, var(--color-secondary) 18%, rgba(255, 255, 255, 0.04));
}

.kg-panel.is-fullscreen .kg-content { min-height: calc(100vh - 104px); }

.kg-panel.is-fullscreen .kg-main,
.kg-panel.is-fullscreen .kg-json,
.kg-panel.is-fullscreen .graph-2d-wrapper,
.kg-panel.is-fullscreen .graph-2d,
.kg-panel.is-fullscreen .graph-text {
  min-height: calc(100vh - 150px);
  height: calc(100vh - 150px);
}

@media (max-width: 1280px) {
  .kg-content.json-open { grid-template-columns: minmax(0, 1fr); }
  .kg-json { min-height: 260px; }
  .kg-ops-panel { width: 236px; }
}

@media (max-width: 980px) {
  .graph-2d-wrapper {
    flex-direction: column;
    height: auto;
    min-height: 840px;
  }

  .graph-2d {
    min-height: 540px;
    height: 540px;
  }

  .kg-ops-panel {
    width: 100%;
    border-left: none;
    border-top: 1px solid var(--kg-panel-border);
  }
}
</style>
