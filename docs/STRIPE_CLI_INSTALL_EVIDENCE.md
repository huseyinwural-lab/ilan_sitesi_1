# STRIPE_CLI_INSTALL_EVIDENCE

**Tarih:** 2026-02-22 01:20:30 UTC

## Kurulum
```
curl -L -o /tmp/stripe.tar.gz https://github.com/stripe/stripe-cli/releases/download/v1.35.1/stripe_1.35.1_linux_arm64.tar.gz
sudo mv /tmp/stripe /usr/local/bin/stripe
```

## Versiyon
```
stripe --version
# stripe version 1.35.1
```

## Auth
`stripe listen --api-key sk_test_emergent` denemesi **401 Invalid API Key** döndü.
