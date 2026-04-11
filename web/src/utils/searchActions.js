import { getChatMessage } from '@/api/ai';
import { trackHistoryEvent } from '@/api/history';

const normalizeText = (value) =>
  String(value || '')
    .replace(/\s+/g, ' ')
    .trim();

const buildSearchText = (...parts) =>
  parts
    .map((part) => normalizeText(part))
    .filter(Boolean)
    .join('\n');

const getOriginRoute = (fallbackRoute) => {
  if (fallbackRoute) return fallbackRoute;
  if (typeof window === 'undefined') return null;
  return `${window.location.pathname}${window.location.search}`;
};

const shouldTrack = (options = {}) => {
  if (typeof options.track === 'boolean') return options.track;
  if (typeof window === 'undefined') return false;
  return Boolean(window.localStorage?.getItem('token'));
};

export async function trackUnifiedSearchResultClick(item, options = {}) {
  if (!item || !shouldTrack(options)) return;

  const query = normalizeText(options.query);
  const source = normalizeText(options.source) || 'search_results';
  const originRoute = getOriginRoute(options.originRoute);
  const searchPayload = {
    domain: 'search',
    event_type: 'result_clicked',
    subject_type: item.subject_type || `${item.source_type || 'search'}_result`,
    subject_id: item.subject_id || null,
    title: item.title || query || '搜索结果',
    subtitle: item.subtitle || null,
    summary: item.description || null,
    route_path: item.route_path || originRoute,
    external_url: item.external_url || null,
    icon: 'search',
    search_text: buildSearchText(query, item.title, item.subtitle, item.description),
    extra: {
      query: query || null,
      source,
      source_route: originRoute,
      result_group: item.group || null,
      result_source_type: item.source_type || null,
      result_action_type: item.action_type || null,
      result_route_path: item.route_path || null,
      result_external_url: item.external_url || null,
      matched_by: item.extra?.matched_by || null,
      published_at: item.published_at || null,
    },
  };

  const tasks = [trackHistoryEvent(searchPayload).catch(() => {})];

  if (item.action_type === 'external' && item.external_url) {
    const isPolicy = item.source_type === 'policy';
    tasks.push(
      trackHistoryEvent({
        domain: isPolicy ? 'policy_browse' : 'article_browse',
        event_type: 'opened_external',
        subject_type: isPolicy ? 'external_policy_article' : 'news_article',
        title: item.title || query || '搜索结果',
        subtitle: item.subtitle || null,
        summary: item.description || null,
        route_path: originRoute,
        external_url: item.external_url,
        icon: isPolicy ? 'policy' : 'news',
        search_text: buildSearchText(query, item.title, item.subtitle, item.description),
        extra: {
          query: query || null,
          source,
          result_group: item.group || null,
          result_source_type: item.source_type || null,
          published_at: item.published_at || null,
        },
      }).catch(() => {})
    );
  }

  await Promise.all(tasks);
}

export async function openUnifiedSearchResult(router, item, options = {}) {
  if (!item) return;
  void trackUnifiedSearchResultClick(item, options);

  if (item.action_type === 'restore_chat' && item.subject_id) {
    const res = await getChatMessage(item.subject_id);
    sessionStorage.setItem('restoredChatMessage', JSON.stringify(res.data));
    await router.push('/home');
    return;
  }

  if (item.action_type === 'route' && item.route_path) {
    await router.push(item.route_path);
    return;
  }

  if (item.action_type === 'external' && item.external_url) {
    window.open(item.external_url, '_blank');
  }
}
