# DEALER_PORTAL_CHUNK_ASSERTION

## Amaç
Dealer login sonrası chunk yükleme izolasyon kanıtı.

## Beklenen
- Dealer chunk request > 0
- Backoffice chunk request = 0

## Sonuç
✅ PASS

## Network Evidence (özet)
- Dealer portal chunk loaded: `src_portals_dealer_DealerPortalApp_jsx.chunk.js`
- Backoffice chunks: none
