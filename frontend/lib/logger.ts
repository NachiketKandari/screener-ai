const isDev = process.env.NODE_ENV === "development";

function formatTime(): string {
  return new Date().toISOString();
}

export const logger = {
  info(msg: string, data?: Record<string, unknown>) {
    if (isDev) {
      console.info(`[${formatTime()}] INFO: ${msg}`, data || "");
    } else {
      console.info(JSON.stringify({ time: formatTime(), level: "INFO", msg, ...data }));
    }
  },
  warn(msg: string, data?: Record<string, unknown>) {
    if (isDev) {
      console.warn(`[${formatTime()}] WARN: ${msg}`, data || "");
    } else {
      console.warn(JSON.stringify({ time: formatTime(), level: "WARN", msg, ...data }));
    }
  },
  error(msg: string, err?: Error, data?: Record<string, unknown>) {
    if (isDev) {
      console.error(`[${formatTime()}] ERROR: ${msg}`, err?.message || "", data || "");
    } else {
      console.error(JSON.stringify({ time: formatTime(), level: "ERROR", msg, error: err?.message, ...data }));
    }
  },
};
