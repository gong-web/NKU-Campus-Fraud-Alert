/** 格式化工具集。统一文本展示风格。 */

/**
 * 把 ISO 8601 时间字符串转成本地时区下的 "YYYY-MM-DD HH:mm:ss"。
 * `null` / `undefined` / 空串返回 `"-"`。
 */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "-";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const pad = (n: number): string => n.toString().padStart(2, "0");
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
    `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  );
}

/** 用千分位格式化数字（金额展示）。 */
export function formatNumber(n: number): string {
  return new Intl.NumberFormat("zh-CN").format(n);
}

/** 把 ISO 时间转成 "x 分钟前 / x 小时前 / x 天前" 的相对描述。 */
export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return "-";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const diff = Date.now() - d.getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${Math.max(1, sec)} 秒前`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day} 天前`;
  return formatDateTime(iso);
}
