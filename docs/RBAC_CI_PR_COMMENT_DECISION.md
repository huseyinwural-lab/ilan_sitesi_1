# RBAC_CI_PR_COMMENT_DECISION

**Tarih:** 2026-02-24 13:46:00 UTC
**Karar:** Eklenecek ✅

## Yaklaşım (Minimal)
- GitHub Actions job, RBAC coverage script çıktısını PR comment olarak yazar.
- PASS: kısa özet (coverage OK)
- FAIL: eksik endpoint listesi (detaylı)

## Uygulama
- Workflow: `.github/workflows/rbac-coverage.yml`
- Adım: `actions/github-script@v7` ile PR comment
- Çıktı kaynağı: `rbac_output.txt`

## Not
- Yorum spam’ini azaltmak için sadece PR event’lerinde yorum yapılır.
