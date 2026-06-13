export function filenameFromContentDisposition(
  contentDisposition: string | undefined,
  fallbackFilename: string,
): string {
  if (!contentDisposition) return fallbackFilename;

  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(contentDisposition);
  if (encoded?.[1]) {
    try {
      return decodeURIComponent(encoded[1]);
    } catch {
      return fallbackFilename;
    }
  }

  const plain = /filename="?([^";]+)"?/i.exec(contentDisposition);
  return plain?.[1] || fallbackFilename;
}

export function downloadBlob(
  blob: Blob,
  contentDisposition: string | undefined,
  fallbackFilename: string,
): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filenameFromContentDisposition(
    contentDisposition,
    fallbackFilename,
  );
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}
