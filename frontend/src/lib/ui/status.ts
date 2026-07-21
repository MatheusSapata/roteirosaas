export type StatusTone = "success" | "warning" | "info" | "danger" | "neutral";

export const statusToneClasses: Record<StatusTone, string> = {
  success: "bg-status-success text-status-success-foreground",
  warning: "bg-status-warning text-status-warning-foreground",
  info: "bg-status-info text-status-info-foreground",
  danger: "bg-status-danger text-status-danger-foreground",
  neutral: "bg-status-neutral text-status-neutral-foreground"
};

export const statusTextClasses: Record<StatusTone, string> = {
  success: "text-status-success-foreground",
  warning: "text-status-warning-foreground",
  info: "text-status-info-foreground",
  danger: "text-status-danger-foreground",
  neutral: "text-status-neutral-foreground"
};

export const statusDotClasses: Record<StatusTone, string> = {
  success: "bg-status-success-foreground",
  warning: "bg-status-warning-foreground",
  info: "bg-status-info-foreground",
  danger: "bg-status-danger-foreground",
  neutral: "bg-status-neutral-foreground"
};

export const getStatusToneClasses = (tone: StatusTone = "neutral") => statusToneClasses[tone];
