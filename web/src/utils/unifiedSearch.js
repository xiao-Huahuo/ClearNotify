export const SEARCH_TYPE_OPTIONS = [
  { value: 'history', label: '历史' },
  { value: 'agent', label: '智能体' },
  { value: 'policy', label: '政策' },
  { value: 'news', label: '时事' },
];

export const SEARCH_TYPE_VALUES = SEARCH_TYPE_OPTIONS.map((item) => item.value);

const SEARCH_TYPE_SET = new Set(SEARCH_TYPE_VALUES);

export const normalizeSearchTypes = (value) => {
  const rawValues = Array.isArray(value) ? value : [value];
  const valueSet = new Set();

  rawValues
    .flatMap((item) => String(item || '').split(','))
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean)
    .forEach((item) => {
      if (SEARCH_TYPE_SET.has(item)) valueSet.add(item);
    });

  return SEARCH_TYPE_VALUES.filter((item) => valueSet.has(item));
};

export const serializeSearchTypes = (value) => {
  const normalized = normalizeSearchTypes(value);
  if (!normalized.length || normalized.length === SEARCH_TYPE_VALUES.length) return '';
  return normalized.join(',');
};

export const areSearchTypesEqual = (left, right) =>
  serializeSearchTypes(left) === serializeSearchTypes(right) ||
  normalizeSearchTypes(left).join(',') === normalizeSearchTypes(right).join(',');

export const buildSearchRouteQuery = (query, types) => {
  const nextQuery = {};
  const normalizedQuery = String(query || '').trim();
  if (normalizedQuery) nextQuery.q = normalizedQuery;

  const serializedTypes = serializeSearchTypes(types);
  if (serializedTypes) nextQuery.types = serializedTypes;

  return nextQuery;
};

export const matchesSearchTypes = (item, types, options = {}) => {
  const { keepSearchHistory = false } = options;
  const normalized = normalizeSearchTypes(types);

  if (!normalized.length || normalized.length === SEARCH_TYPE_VALUES.length) return true;
  if (keepSearchHistory && item?.group === 'recent_search') return true;

  return normalized.includes(String(item?.source_type || '').trim().toLowerCase());
};

export const getSearchSourceLabel = (sourceType) => {
  if (sourceType === 'history') return '历史';
  if (sourceType === 'agent') return '智能体';
  if (sourceType === 'policy') return '政策';
  return '时事';
};
