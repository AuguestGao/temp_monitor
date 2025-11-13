/**
 * Convert a local datetime string (from datetime-local input) to UTC ISO string
 * @param localDateTimeString - Format: "YYYY-MM-DDTHH:mm" (local time)
 * @returns UTC ISO string format: "YYYY-MM-DDTHH:mm:ss.sssZ"
 */
export function localToUTC(localDateTimeString: string): string {
  if (!localDateTimeString) {
    return '';
  }
  
  // Create a date object from the local datetime string
  // The datetime-local input gives us a string like "2025-11-04T00:00"
  // which is in the user's local timezone
  const localDate = new Date(localDateTimeString);
  
  // Convert to UTC ISO string
  return localDate.toISOString();
}

/**
 * Format a date to datetime-local input format (YYYY-MM-DDTHH:mm)
 * @param date - Date object
 * @returns String in format "YYYY-MM-DDTHH:mm"
 */
export function formatForDateTimeLocal(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

