const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function setupProxy(app) {
  const target = process.env.SITEMAP_PROXY_TARGET || 'http://127.0.0.1:8001';

  app.use(
    ['/sitemap.xml', '/robots.txt', '/sitemaps'],
    createProxyMiddleware({
      target,
      changeOrigin: true,
      secure: false,
      logLevel: 'warn',
    }),
  );
};
