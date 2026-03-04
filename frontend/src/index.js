import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import ErrorBoundary from "@/components/ErrorBoundary";

const ROUTE_SCOPED_DOM_NESTING_WARNINGS = [
  'validatedomnesting',
  '<tr>',
  '<tbody>',
  '<span>',
  '<option>',
  '<select>',
  'hydration',
];

const shouldSuppressRouteWarning = () => {
  const path = window.location.pathname || '';
  return path.startsWith('/dealer') || path.startsWith('/admin/user-interface-design') || path.startsWith('/admin/ui-designer');
};

const originalConsoleError = console.error.bind(console);
console.error = (...args) => {
  const message = args.map((arg) => String(arg || '')).join(' ').toLowerCase();
  const isKnownDomWarning = ROUTE_SCOPED_DOM_NESTING_WARNINGS.every((token) => message.includes(token))
    || (message.includes('validatedomnesting') && (message.includes('<tr>') || message.includes('<tbody>') || message.includes('<option>') || message.includes('<select>')));

  if (shouldSuppressRouteWarning() && isKnownDomWarning) {
    return;
  }

  originalConsoleError(...args);
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.getRegistrations()
      .then((registrations) => Promise.all(registrations.map((registration) => registration.unregister())))
      .catch(() => {});
  });
}
