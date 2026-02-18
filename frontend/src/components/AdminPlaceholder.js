import React from "react";

export default function AdminPlaceholder({
  title,
  description,
  status = "P1",
  note,
  actionLabel,
  actionHref,
  testId,
}) {
  return (
    <div className="space-y-6" data-testid={testId || "admin-placeholder"}>
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900" data-testid="admin-placeholder-title">
              {title}
            </h1>
            <p className="mt-2 text-sm text-gray-500" data-testid="admin-placeholder-description">
              {description}
            </p>
          </div>
          <span
            className="inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700"
            data-testid="admin-placeholder-status"
          >
            {status}
          </span>
        </div>
        {note && (
          <div className="mt-4 rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-700" data-testid="admin-placeholder-note">
            {note}
          </div>
        )}
        {actionLabel && actionHref && (
          <a
            href={actionHref}
            className="mt-4 inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-700"
            data-testid="admin-placeholder-action"
          >
            {actionLabel}
          </a>
        )}
      </div>
    </div>
  );
}
