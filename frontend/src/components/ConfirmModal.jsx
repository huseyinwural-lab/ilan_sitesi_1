import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

export const ConfirmModal = ({
  open,
  onOpenChange,
  title,
  description,
  warningText,
  cancelLabel,
  proceedLabel,
  openRevisionLabel = 'Revizyonu Aç',
  onCancel,
  onProceed,
  conflictItems,
  loading,
  testIdPrefix = 'confirm-modal',
}) => {
  const items = Array.isArray(conflictItems) ? conflictItems : [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid={`${testIdPrefix}-content`}>
        <DialogHeader data-testid={`${testIdPrefix}-header`}>
          <DialogTitle data-testid={`${testIdPrefix}-title`}>{title}</DialogTitle>
          <DialogDescription data-testid={`${testIdPrefix}-description`}>{description}</DialogDescription>
        </DialogHeader>

        {warningText ? (
          <p className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800" data-testid={`${testIdPrefix}-warning`}>
            {warningText}
          </p>
        ) : null}

        <div className="max-h-56 overflow-y-auto rounded-md border bg-slate-50 p-2" data-testid={`${testIdPrefix}-conflict-list`}>
          {items.length === 0 ? (
            <p className="text-xs text-slate-500" data-testid={`${testIdPrefix}-conflict-empty`}>
              Çakışma detayı bulunamadı.
            </p>
          ) : (
            <ul className="space-y-1" data-testid={`${testIdPrefix}-conflict-items`}>
              {items.map((item, index) => (
                <li
                  key={`${testIdPrefix}-conflict-item-${item?.revision_id || index}`}
                  className="rounded border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700"
                  data-testid={`${testIdPrefix}-conflict-item-${index}`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2" data-testid={`${testIdPrefix}-conflict-item-row-${index}`}>
                    <span data-testid={`${testIdPrefix}-conflict-item-text-${index}`}>
                      {String(item?.country || '-').toUpperCase()} / {item?.module || '-'} / {item?.page_type || '-'}
                      {' • '}rev: {item?.revision_id || '-'}
                    </span>
                    {item?.revision_id ? (
                      <a
                        href={`/admin/revisions/${item.revision_id}`}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded border border-slate-300 px-2 py-1 text-[11px] text-slate-700 hover:bg-slate-100"
                        data-testid={`${testIdPrefix}-open-revision-link-${index}`}
                      >
                        {openRevisionLabel}
                      </a>
                    ) : (
                      <span className="text-[11px] text-rose-700" data-testid={`${testIdPrefix}-missing-revision-${index}`}>
                        revision_id eksik
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <DialogFooter data-testid={`${testIdPrefix}-footer`}>
          <button
            type="button"
            className="h-9 rounded border px-3 text-sm"
            onClick={onCancel}
            disabled={loading}
            data-testid={`${testIdPrefix}-cancel-button`}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className="h-9 rounded bg-slate-900 px-3 text-sm text-white disabled:cursor-not-allowed disabled:opacity-60"
            onClick={onProceed}
            disabled={loading}
            data-testid={`${testIdPrefix}-proceed-button`}
          >
            {loading ? 'İşleniyor...' : proceedLabel}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
