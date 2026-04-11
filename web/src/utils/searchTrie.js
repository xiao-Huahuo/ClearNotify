const createNode = () => ({
  children: new Map(),
  items: [],
});

const normalizeLabel = (value) =>
  String(value || '')
    .trim()
    .toLowerCase();

const splitAliasParts = (value) =>
  normalizeLabel(value)
    .split(/[\s,，。；;、/|()[\]{}<>《》“”"'‘’!！?？:+\-]+/g)
    .map((item) => item.trim())
    .filter(Boolean);

const isCjkText = (value) => /[\u3400-\u9fff]/.test(value);

const collectAliases = (item) => {
  const rawValues = [
    item?.title,
    item?.subtitle,
    item?.description,
    item?.extra?.query,
    item?.extra?.category,
    item?.extra?.tags,
  ];

  const aliases = new Set();

  rawValues.forEach((rawValue) => {
    splitAliasParts(rawValue).forEach((part) => {
      if (part.length >= 1) aliases.add(part);
      if (!isCjkText(part)) return;
      for (let index = 1; index < part.length; index += 1) {
        const suffix = part.slice(index);
        if (suffix.length >= 2) aliases.add(suffix);
      }
    });
  });

  return [...aliases];
};

export function buildSearchTrie(items = [], maxBucketSize = 12) {
  const root = createNode();

  items.forEach((item, index) => {
    const aliases = collectAliases(item);
    aliases.forEach((label) => {
      if (!label) return;

      let node = root;
      for (const char of label) {
        if (!node.children.has(char)) {
          node.children.set(char, createNode());
        }
        node = node.children.get(char);
        if (node.items.length < maxBucketSize) {
          node.items.push(index);
        }
      }
    });
  });

  return root;
}

export function trieSearch(root, items, query, limit = 6) {
  const normalizedQuery = normalizeLabel(query);
  if (!root || !normalizedQuery) return [];

  let node = root;
  for (const char of normalizedQuery) {
    node = node.children.get(char);
    if (!node) return [];
  }

  return node.items
    .map((index) => items[index])
    .filter(Boolean)
    .filter((item, index, array) => array.findIndex((entry) => entry === item) === index)
    .slice(0, limit);
}
