export function formatSecondsToTime(totalSeconds: number | null | undefined): string {
  const safeSeconds = Math.max(0, Math.floor(totalSeconds ?? 0))
  const hours = Math.floor(safeSeconds / 3600)
  const minutes = Math.floor((safeSeconds % 3600) / 60)
  const seconds = safeSeconds % 60

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }

  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

export function parseUtcDate(dateStr: string | null | undefined): number {
  if (!dateStr) return NaN
  // If the string contains 'T' but no 'Z' and no offset, assume UTC and append 'Z'
  if (dateStr.includes('T') && !dateStr.includes('Z') && !/[+-]\d{2}(:?\d{2})?$/.test(dateStr)) {
    return Date.parse(dateStr + 'Z')
  }
  return Date.parse(dateStr)
}
