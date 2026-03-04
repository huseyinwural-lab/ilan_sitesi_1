import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function SiteFooter({ layoutOverride, refreshToken }) {
  const { language } = useLanguage();
  const [layout, setLayout] = useState(null);

  const renderFallbackFooter = () => (
    <footer className="border-t bg-[var(--footer-bg)] text-[var(--footer-text)]" data-testid="site-footer">
      <div className="mx-auto max-w-6xl px-4 py-10 space-y-6">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4" data-testid="site-footer-fallback-links">
          <div data-testid="site-footer-fallback-trust">
            <div className="text-sm font-semibold">Güven & Politika</div>
            <ul className="mt-2 space-y-2 text-sm">
              <li><Link to="/trust" className="text-[var(--link)] hover:text-[var(--link-hover)]" data-testid="site-footer-fallback-link-trust">Merkez</Link></li>
              <li><Link to="/bilgi/gizlilik-politikasi" className="text-[var(--link)] hover:text-[var(--link-hover)]" data-testid="site-footer-fallback-link-privacy">Gizlilik Politikası</Link></li>
            </ul>
          </div>
          <div data-testid="site-footer-fallback-corporate">
            <div className="text-sm font-semibold">Kurumsal</div>
            <ul className="mt-2 space-y-2 text-sm">
              <li><Link to="/kurumsal" className="text-[var(--link)] hover:text-[var(--link-hover)]" data-testid="site-footer-fallback-link-corporate">Kurumsal Sayfalar</Link></li>
              <li><Link to="/bilgi/magaza-cozumleri" className="text-[var(--link)] hover:text-[var(--link-hover)]" data-testid="site-footer-fallback-link-store">Mağaza Çözümleri</Link></li>
            </ul>
          </div>
          <div data-testid="site-footer-fallback-seo">
            <div className="text-sm font-semibold">Bilgi Merkezi</div>
            <ul className="mt-2 space-y-2 text-sm">
              <li><Link to="/seo" className="text-[var(--link)] hover:text-[var(--link-hover)]" data-testid="site-footer-fallback-link-seo">SEO Merkezi</Link></li>
              <li><Link to="/bilgi/yardim-merkezi" className="text-[var(--link)] hover:text-[var(--link-hover)]" data-testid="site-footer-fallback-link-help">Yardım Merkezi</Link></li>
            </ul>
          </div>
          <div data-testid="site-footer-fallback-system">
            <div className="text-sm font-semibold">Sistem</div>
            <ul className="mt-2 space-y-2 text-sm">
              <li><Link to="/500" className="text-[var(--link)] hover:text-[var(--link-hover)]" data-testid="site-footer-fallback-link-500">500 Hata Sayfası</Link></li>
              <li><Link to="/maintenance" className="text-[var(--link)] hover:text-[var(--link-hover)]" data-testid="site-footer-fallback-link-maintenance">Bakım Sayfası</Link></li>
            </ul>
          </div>
        </div>
        <div className="text-sm text-[var(--footer-text)]" data-testid="site-footer-fallback-copyright">
          © 2026 Annoncia
        </div>
      </div>
    </footer>
  );

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

  const rows = Array.isArray(layout?.rows) ? layout.rows : [];
  const hasRenderableRows = rows.some((row) => {
    const columns = Array.isArray(row?.columns) ? row.columns : [];
    return columns.some((col) => {
      if (col?.type === 'link_group' || col?.type === 'social') {
        return Array.isArray(col?.links) && col.links.length > 0;
      }
      if (typeof col?.text === 'string') {
        return col.text.trim().length > 0;
      }
      if (col?.text && typeof col.text === 'object') {
        return Object.values(col.text).some((value) => typeof value === 'string' && value.trim().length > 0);
      }
      return Boolean(col?.title);
    });
  });

  const hasMenuLinkGroups = rows.some((row) => {
    const columns = Array.isArray(row?.columns) ? row.columns : [];
    return columns.some((col) => col?.type === 'link_group' && Array.isArray(col?.links) && col.links.length > 0);
  });

  const menuLinkCount = rows.reduce((total, row) => {
    const columns = Array.isArray(row?.columns) ? row.columns : [];
    const rowLinks = columns.reduce((sum, col) => {
      if ((col?.type === 'link_group' || col?.type === 'social') && Array.isArray(col?.links)) {
        return sum + col.links.length;
      }
      return sum;
    }, 0);
    return total + rowLinks;
  }, 0);

  if (!layout || !hasRenderableRows || !hasMenuLinkGroups || menuLinkCount < 6) {
    return renderFallbackFooter();
  }

  return (
    <footer className="border-t bg-[var(--footer-bg)] text-[var(--footer-text)]" data-testid="site-footer">
      <div className="mx-auto max-w-6xl px-4 py-10 space-y-8">
        {rows.map((row, rowIndex) => (
          <div
            key={rowIndex}
            className="grid gap-6"
            style={{ gridTemplateColumns: `repeat(${Math.min(row.columns?.length || 1, 5)}, minmax(0, 1fr))` }}
            data-testid={`site-footer-row-${rowIndex}`}
          >
            {(row.columns || []).map((col, colIndex) => {
              const type = col.type || 'text';
              if (type === 'link_group') {
                return (
                  <div key={colIndex} data-testid={`site-footer-col-${rowIndex}-${colIndex}`}>
                    <div className="text-sm font-semibold text-[var(--footer-text)]" data-testid={`site-footer-col-title-${rowIndex}-${colIndex}`}>
                      {col.title}
                    </div>
                    <ul className="mt-3 space-y-2 text-sm text-[var(--footer-text)]">
                      {(col.links || []).map((link, linkIndex) => {
                        if (link.type === 'info') {
                          return (
                            <li key={linkIndex}>
                              <Link
                                to={`/bilgi/${link.target}`}
                                className="text-[var(--link)] hover:text-[var(--link-hover)]"
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
                              className="text-[var(--link)] hover:text-[var(--link-hover)]"
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
                    <div className="text-sm font-semibold text-[var(--footer-text)]" data-testid={`site-footer-col-title-${rowIndex}-${colIndex}`}>
                      {col.title}
                    </div>
                    <ul className="mt-3 space-y-2 text-sm text-[var(--footer-text)]">
                      {(col.links || []).map((link, linkIndex) => (
                        <li key={linkIndex}>
                          <a
                            href={link.target}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[var(--link)] hover:text-[var(--link-hover)]"
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
                  <div className="text-sm font-semibold text-[var(--footer-text)]" data-testid={`site-footer-col-title-${rowIndex}-${colIndex}`}>
                    {col.title}
                  </div>
                  <div className="mt-3 text-sm text-[var(--footer-text)]" data-testid={`site-footer-col-text-${rowIndex}-${colIndex}`}>
                    {(() => {
                      const textObj = col.text && typeof col.text === 'object' ? col.text : {};
                      const value = textObj[language] || textObj.tr || textObj.de || textObj.fr || (typeof col.text === 'string' ? col.text : '');
                      return value || '';
                    })()}
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
