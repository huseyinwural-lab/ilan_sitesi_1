# P25: Reveal Optimization Plan

## 1. Goal
Increase `Detail View -> Reveal Click` conversion from 2% to 5%.

## 2. Friction Points
*   Button location is below the fold on mobile.
*   Users fear spam if they reveal.
*   Users don't trust the seller.

## 3. Optimization Tactics

### 3.1. Sticky CTA (Mobile)
*   On scroll, "Show Phone" and "Message" buttons stick to the bottom of the screen.

### 3.2. Trust Micro-Copy
*   Add below button: *"Your number is kept private."* (If using internal relay - V2).
*   Add: *"Identity Verified"* checkmark next to button.

### 3.3. Interstitial Login
*   Allow clicking "Show Phone" -> If not logged in, show Modal "Login to see number" instead of full redirect. Keep context.

## 4. Metrics
*   `reveal_conversion_rate`
*   `bounce_rate_on_login`
