<template>
  <div class="card" :class="toneClass">
    <div v-if="icon || title" class="card-header">
      <div v-if="icon" class="card-icon-wrap">
        <Icon :name="icon" :size="20" />
      </div>
      <div class="card-title-area">
        <h3 v-if="title">{{ title }}</h3>
        <p v-if="subtitle" class="card-subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="card-actions">
        <slot name="actions" />
      </div>
    </div>
    <div class="card-body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="card-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import Icon from './Icons.vue';

const props = defineProps({
  title: { type: String },
  subtitle: { type: String },
  icon: { type: String },
  tone: { type: String, default: 'default' } // default, primary, danger, warning, success
});

const toneClass = computed(() => `tone-${props.tone}`);
</script>

<style scoped>
.card {
  background: var(--panel);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.08);
  padding: 20px;
  border-left: 4px solid transparent;
}

.tone-default { border-left-color: var(--line); }
.tone-primary { border-left-color: var(--primary); }
.tone-danger { border-left-color: var(--danger); }
.tone-warning { border-left-color: var(--warn); }
.tone-success { border-left-color: var(--ok); }

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 15px;
}

.card-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.tone-default .card-icon-wrap { background: var(--line); }
.tone-primary .card-icon-wrap { background: var(--primary); }
.tone-danger .card-icon-wrap { background: var(--danger); }
.tone-warning .card-icon-wrap { background: var(--warn); }
.tone-success .card-icon-wrap { background: var(--ok); }

.card-title-area h3 {
  margin: 0;
  font-size: 16px;
  color: var(--ink);
}

.card-subtitle {
  margin: 3px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.card-actions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

.card-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
  font-size: 13px;
  color: var(--primary);
  cursor: pointer;
}
</style>