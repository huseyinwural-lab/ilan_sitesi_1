import { Fragment } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

const LABELS = {
  admin: 'Admin',
  users: 'Kullanıcılar',
  countries: 'Ülkeler',
  categories: 'Kategoriler',
  attributes: 'Özellikler',
  'feature-flags': 'Özellik Bayrakları',
  'audit-logs': 'Denetim Kayıtları',
  plans: 'Plans',
  billing: 'Billing',
  'master-data': 'Master Data',
  vehicles: 'Vehicle Makes',
};

function labelFor(seg) {
  return LABELS[seg] || seg;
}

export default function AdminBreadcrumbs({ overrideItems }) {
  const location = useLocation();

  const segments = location.pathname.split('/').filter(Boolean);
  if (segments[0] !== 'admin') return null;

  const items = overrideItems || segments.map((seg, idx) => {
    const to = '/' + segments.slice(0, idx + 1).join('/');
    return { seg, to, label: labelFor(seg) };
  });

  return (
    <Breadcrumb>
      <BreadcrumbList>
        {items.map((it, idx) => {
          const isLast = idx === items.length - 1;
          return (
            <Fragment key={it.to}>
              <BreadcrumbItem>
                {isLast ? (
                  <BreadcrumbPage>{it.label}</BreadcrumbPage>
                ) : (
                  <BreadcrumbLink asChild>
                    <Link to={it.to}>{it.label}</Link>
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
              {!isLast && <BreadcrumbSeparator />}
            </Fragment>
          );
        })}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
