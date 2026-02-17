# Vehicle Wizard v2 — E2E Validation Scenarios

## Senaryo 1 (success)
- otomobil: segment→make→model→year→temel bilgiler→foto(>=3 & >=800x600)→publish

## Senaryo 2 (enforcement)
- master data dışı make/model dene → backend reject

## Senaryo 3 (foto)
- foto < 3 → UI hard-block

## Senaryo 4 (country switch)
- DE/FR switch → wizard context korunur, makes/models çağrıları country param ile yapılır

> Not: Elektrikli ayrı segment değil; fuel_type üzerinden test edilir.
