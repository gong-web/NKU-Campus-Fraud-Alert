<script setup lang="ts" generic="T extends Record<string, unknown>">
import AppEmpty from "./AppEmpty.vue";
import AppSkeleton from "./AppSkeleton.vue";

interface Column<U> {
  key: keyof U & string;
  title: string;
  width?: string;
  align?: "left" | "right" | "center";
  formatter?: (row: U) => string | number;
  /** 等宽数字列（如 ID、IP） */
  mono?: boolean;
}

interface Props {
  rows: T[];
  columns: Column<T>[];
  loading?: boolean;
  rowKey?: keyof T & string;
  emptyTitle?: string;
  emptyHint?: string;
  caption?: string;
  /** 行斑马纹（金融/审计场景默认开） */
  zebra?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  emptyTitle: "暂无数据",
  emptyHint: "",
  caption: "",
  zebra: false,
});

defineEmits<{
  "row-click": [row: T];
}>();

function cellValue(row: T, col: Column<T>): string | number {
  if (col.formatter) return col.formatter(row);
  const v = row[col.key];
  return v == null ? "" : String(v);
}

function rowIdentifier(row: T, idx: number): string | number {
  if (props.rowKey) {
    const v = row[props.rowKey as keyof T];
    return v == null ? idx : String(v);
  }
  return idx;
}
</script>

<template>
  <div
    class="app-table"
    :class="{ 'app-table--zebra': zebra }"
  >
    <p
      v-if="caption"
      class="app-table__caption"
    >
      {{ caption }}
    </p>
    <div
      v-if="loading"
      class="app-table__loading"
    >
      <AppSkeleton :rows="6" />
    </div>
    <div
      v-else-if="rows.length === 0"
      class="app-table__empty"
    >
      <AppEmpty
        :title="emptyTitle"
        :hint="emptyHint"
        illustration="default"
      >
        <template
          v-if="$slots['empty-action']"
          #action
        >
          <slot name="empty-action" />
        </template>
      </AppEmpty>
    </div>
    <div
      v-else
      class="app-table__scroll"
      tabindex="0"
    >
      <table
        class="app-table__el"
        role="grid"
      >
        <thead>
          <tr>
            <th
              v-for="c in columns"
              :key="c.key"
              :style="{ width: c.width, textAlign: c.align || 'left' }"
              :class="{ 'is-mono': c.mono }"
              scope="col"
            >
              {{ c.title }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in rows"
            :key="rowIdentifier(row, idx)"
            @click="$emit('row-click', row)"
          >
            <td
              v-for="c in columns"
              :key="c.key"
              :style="{ textAlign: c.align || 'left' }"
              :class="{ 'is-mono': c.mono }"
            >
              <slot
                :name="`cell-${c.key}`"
                :row="row"
              >
                {{ cellValue(row, c) }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div
      v-if="$slots.footer"
      class="app-table__footer"
    >
      <slot name="footer" />
    </div>
  </div>
</template>

<style scoped>
.app-table {
  position: relative;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-low);
}

.app-table::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
    to right,
    var(--color-brand-500) 0,
    var(--color-brand-500) 56px,
    var(--color-gold-400) 56px,
    var(--color-gold-400) 72px,
    transparent 72px
  );
  z-index: 3;
}

.app-table__caption {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
}

.app-table__scroll {
  overflow-x: auto;
}

.app-table__el {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.app-table__el th,
.app-table__el td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border-soft);
  vertical-align: middle;
}

.app-table__el thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: linear-gradient(180deg, #fafbfd 0%, #f1f3f8 100%);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-semibold);
  font-size: 11.5px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-align: start;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
  box-shadow: inset 0 -1px 0 var(--color-border);
}

.app-table__el thead th.is-mono,
.app-table__el tbody td.is-mono {
  font-family: var(--font-family-mono);
  font-variant-numeric: tabular-nums slashed-zero;
  letter-spacing: 0.01em;
}

.app-table__el tbody tr {
  cursor: default;
  transition: background var(--duration-fast) var(--easing-out);
}

.app-table__el tbody tr:hover {
  background:
    linear-gradient(90deg, rgb(134 38 51 / 4%) 0%, rgb(134 38 51 / 1%) 100%);
  box-shadow: inset 3px 0 0 var(--color-brand-400);
}

.app-table--zebra tbody tr:nth-child(even) {
  background: var(--color-bg-soft);
}

.app-table--zebra tbody tr:nth-child(even):hover {
  background: var(--color-neutral-100);
}

.app-table__el tbody tr:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: -2px;
}

.app-table__el tbody tr:last-child td {
  border-bottom: none;
}

.app-table__loading,
.app-table__empty {
  padding: var(--space-5);
}

.app-table__footer {
  padding: 10px var(--space-4);
  border-top: 1px solid var(--color-border);
  background: linear-gradient(180deg, var(--color-bg) 0%, var(--color-bg-soft) 100%);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: var(--space-3);
}

.app-table__footer > :first-child { justify-self: start; }
.app-table__footer > :last-child  { justify-self: end; }
</style>
