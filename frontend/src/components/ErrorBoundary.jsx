import React from 'react';

import ServerErrorPage from '@/pages/public/ServerErrorPage';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    if (this.props.onError) {
      this.props.onError(error, info);
    }
    console.error('ErrorBoundary caught an error', error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    const { hasError, error } = this.state;
    if (hasError) {
      return (
        <div className="mx-auto max-w-2xl rounded-lg border bg-[var(--bg-surface)] p-6 text-sm" data-testid="error-boundary">
          <div className="text-lg font-semibold text-[var(--text-primary)]" data-testid="error-boundary-title">
            Bir şeyler ters gitti
          </div>
          <div className="mt-2 text-[var(--text-secondary)]" data-testid="error-boundary-message">
            Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.
          </div>
          {error && (
            <div className="mt-3 text-xs text-[var(--text-secondary)]" data-testid="error-boundary-detail">
              {error.message}
            </div>
          )}
          <button
            type="button"
            onClick={this.handleReset}
            className="mt-4 h-9 rounded-md bg-[var(--color-primary)] px-4 text-[var(--text-inverse)]"
            data-testid="error-boundary-reset"
          >
            Tekrar dene
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
