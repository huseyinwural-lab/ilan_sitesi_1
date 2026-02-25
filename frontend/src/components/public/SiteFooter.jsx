import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function SiteFooter({ layoutOverride, refreshToken }) {
  const { language } = useLanguage();
  const [layout, setLayout] = useState(null);

  useEffect(() => {
    if (layoutOverride !== undefined) {
      setLayout(layoutOverride);
    }
  }, [layoutOverride]);

  useEffect(() => {
    if (layoutOverride !== undefined) return;
    let active = true;
    fetch(`${API}/site/footer`)
      .then((res) => res.json())
      .then((data) => {
        if (!active) return;
        setLayout(data?.layout || null);
      })
      .catch(() => {
        if (!active) return;
        setLayout(null);
      });
    return () => {
      active = false;
    };
  }, [layoutOverride, refreshToken]);

  if (!layout) {
    return (
      <footer className="border-t bg-white" data-testid="site-footer">
        <div className="mx-auto max-w-6xl px-4 py-10 text-sm text-[#415A77]">
          © 2026 Annoncia
        </div>
      </footer>
    );
  }

  const rows = Array.isArray(layout.rows) ? layout.rows : [];

  return (
    <footer className="border-t bg-white" data-testid="site-footer">
      <div className="mx-auto max-w-6xl px-4 py-10 space-y-8">
        {rows.map((row, rowIndex) => (
          <div
            key={rowIndex}
            className={`grid gap-6 md:grid-cols-${Math.min(row.columns?.length || 1, 5)}`}
            data-testid={`site-footer-row-${rowIndex}`}
          >
            {(row.columns || []).map((col, colIndex) => {
              const type = col.type || 'text';
              if (type === 'link_group') {
                return (
                  <div key={colIndex} data-testid={`site-footer-col-${rowIndex}-${colIndex}`}>
                    <div className="text-sm font-semibold text-[#1B263B]" data-testid={`site-footer-col-title-${rowIndex}-${colIndex}`}>
                      {col.title}
                    </div>
                    <ul className="mt-3 space-y-2 text-sm text-[#415A77]">
                      {(col.links || []).map((link, linkIndex) => {
                        if (link.type === 'info') {
                          return (
                            <li key={linkIndex}>
                              <Link
                                to={`/bilgi/${link.target}`}
                                data-testid={`site-footer-link-${rowIndex}-${colIndex}-${linkIndex}`}
                              >
                                {link.label}
                              </Link>
                            </li>
                          );
                        }
                        return (
                          <li key={linkIndex}>
                            <a
                              href={link.target}
                              target="_blank"
                              rel="noreferrer"
                              data-testid={`site-footer-link-${rowIndex}-${colIndex}-${linkIndex}`}
                            >
                              {link.label}
                            </a>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                );
              }
              if (type === 'social') {
                return (
                  <div key={colIndex} data-testid={`site-footer-col-${rowIndex}-${colIndex}`}>
                    <div className="text-sm font-semibold text-[#1B263B]" data-testid={`site-footer-col-title-${rowIndex}-${colIndex}`}>
                      {col.title}
                    </div>
                    <ul className="mt-3 space-y-2 text-sm text-[#415A77]">
                      {(col.links || []).map((link, linkIndex) => (
                        <li key={linkIndex}>
                          <a
                            href={link.target}
                            target="_blank"
                            rel="noreferrer"
                            data-testid={`site-footer-social-${rowIndex}-${colIndex}-${linkIndex}`}
                          >
                            {link.label}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              }
              return (
                <div key={colIndex} data-testid={`site-footer-col-${rowIndex}-${colIndex}`}>
                  <div className="text-sm font-semibold text-[#1B263B]" data-testid={`site-footer-col-title-${rowIndex}-${colIndex}`}>
                    {col.title}
                  </div>
                  <div className="mt-3 text-sm text-[#415A77]" data-testid={`site-footer-col-text-${rowIndex}-${colIndex}`}>
                    {col.text?.[language] || col.text?.tr || col.text || ''}
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </footer>
  );
}
