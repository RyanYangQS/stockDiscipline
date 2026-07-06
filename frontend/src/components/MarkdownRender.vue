<template>
  <div class="markdown-render" v-html="renderedContent"></div>
</template>

<script setup>
import { computed } from 'vue';
import { marked } from 'marked';
import hljs from 'highlight.js';

const props = defineProps({
  content: {
    type: String,
    default: ''
  }
});

// Configure marked options (highlight option is deprecated in v18)
marked.setOptions({
  breaks: true,
  gfm: true
});

// Custom renderer for marked v18 API (receives token objects, not separate params)
const renderer = new marked.Renderer();

// Code block renderer - handles syntax highlighting
renderer.code = function(token) {
  const code = token.text;
  const lang = token.lang;
  let highlighted;

  if (lang && hljs.getLanguage(lang)) {
    try {
      highlighted = hljs.highlight(code, { language: lang }).value;
    } catch (err) {
      highlighted = hljs.highlightAuto(code).value;
    }
  } else {
    highlighted = hljs.highlightAuto(code).value;
  }

  return `<pre><code class="hljs">${highlighted}</code></pre>`;
};

// Link renderer - receives token object in v18, with XSS protection
renderer.link = function(token) {
  const { href, title, text } = token;

  // Security: Only allow http/https URLs to prevent javascript: XSS
  const safeHref = /^https?:\/\//.test(href) ? href : '#';

  // Escape title attribute to prevent XSS
  const titleAttr = title ? ` title="${title.replace(/"/g, '&quot;')}"` : '';

  return `<a href="${safeHref}"${titleAttr} target="_blank" rel="noopener noreferrer">${text}</a>`;
};

// Paragraph renderer - receives token object in v18
renderer.paragraph = function(token) {
  const paragraphText = token.text;

  // Highlight key sections: 盈亏、建议、风险
  const highlightedText = paragraphText
    .replace(/盈亏/g, '<span class="highlight-pnl">$&</span>')
    .replace(/建议/g, '<span class="highlight-advice">$&</span>')
    .replace(/风险/g, '<span class="highlight-risk">$&</span>');

  return `<p>${highlightedText}</p>`;
};

const renderedContent = computed(() => {
  if (!props.content) {
    return '';
  }

  try {
    // Use custom renderer with marked v18 API
    marked.use({ renderer });
    return marked(props.content);
  } catch (err) {
    console.error('Markdown rendering error:', err);
    return `<p>${props.content}</p>`;
  }
});
</script>

<style scoped>
.markdown-render {
  line-height: 1.65;
  color: var(--ink);
}

.markdown-render :deep(h1) {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 16px 0;
  color: var(--ink);
}

.markdown-render :deep(h2) {
  font-size: 20px;
  font-weight: 700;
  margin: 24px 0 12px 0;
  color: var(--ink);
}

.markdown-render :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 20px 0 10px 0;
  color: var(--ink);
}

.markdown-render :deep(h4) {
  font-size: 14px;
  font-weight: 600;
  margin: 16px 0 8px 0;
  color: var(--ink);
}

.markdown-render :deep(p) {
  margin: 0 0 12px 0;
  line-height: 1.7;
}

.markdown-render :deep(ul),
.markdown-render :deep(ol) {
  margin: 0 0 12px 0;
  padding-left: 24px;
}

.markdown-render :deep(li) {
  margin: 4px 0;
  line-height: 1.6;
}

.markdown-render :deep(code) {
  background: var(--line);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-render :deep(pre) {
  background: var(--table-header);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 12px;
  margin: 0 0 12px 0;
  overflow-x: auto;
}

.markdown-render :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.85em;
  line-height: 1.5;
}

.markdown-render :deep(a) {
  color: var(--primary);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
}

.markdown-render :deep(a:hover) {
  border-bottom-color: var(--primary);
}

.markdown-render :deep(a:focus-visible) {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

.markdown-render :deep(blockquote) {
  border-left: 3px solid var(--primary);
  margin: 12px 0;
  padding: 8px 16px;
  background: var(--table-header);
  border-radius: 4px;
}

.markdown-render :deep(blockquote p) {
  margin: 0;
  color: var(--muted);
}

.markdown-render :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

.markdown-render :deep(th),
.markdown-render :deep(td) {
  border: 1px solid var(--line);
  padding: 8px 12px;
  text-align: left;
}

.markdown-render :deep(th) {
  background: var(--table-header);
  font-weight: 600;
  color: var(--muted);
}

.markdown-render :deep(hr) {
  border: none;
  border-top: 1px solid var(--line);
  margin: 20px 0;
}

/* Key section highlights */
.markdown-render :deep(.highlight-pnl) {
  color: var(--primary);
  font-weight: 600;
  background: linear-gradient(to bottom, transparent 0%, transparent 70%, rgba(23, 107, 135, 0.1) 70%);
}

.markdown-render :deep(.highlight-advice) {
  color: var(--ok);
  font-weight: 600;
  background: linear-gradient(to bottom, transparent 0%, transparent 70%, rgba(6, 118, 71, 0.1) 70%);
}

.markdown-render :deep(.highlight-risk) {
  color: var(--danger);
  font-weight: 600;
  background: linear-gradient(to bottom, transparent 0%, transparent 70%, rgba(180, 35, 24, 0.1) 70%);
}
</style>