# P20: Mobile MVP Scope Freeze

## 1. Objective
To launch a high-quality, stable mobile application (iOS & Android) that allows users to discover listings, save favorites, and participate in the affiliate program. **Creation (Posting Ads) and Payments are deferred to v1.1.**

## 2. In-Scope Features (MVP)

### 2.1. Authentication
- **Login**: Email/Password.
- **Register**: Standard registration flow with Referral Code support.
- **Forgot Password**: Link to webview or native flow.
- **Logout**: Secure token revocation.

### 2.2. Discovery (Home & Search)
- **Home Feed**:
    - Showcase Listings (Horizontal Scroll).
    - Special Collections (Urgent, Price Drops).
    - Category Grid.
- **Search & Filter**:
    - Keyword Search.
    - Category Selection.
    - Price Range, City/Country Filter.
- **Listing List**:
    - Infinite Scroll.
    - Simplified Card View (Image, Title, Price, Location, Date).

### 2.3. Listing Detail
- **Gallery**: Swipeable image gallery.
- **Info**: Price, Description, Attributes (Make, Model, Year).
- **Seller**: Basic seller info (Name, Rating).
- **Actions**:
    - Call Seller (Native Phone Dialer).
    - Share Listing (Native Share Sheet).
    - Add to Favorites.

### 2.4. User Engagement
- **Favorites**: View list of saved ads.
- **Affiliate Center (Lite)**:
    - View "My Referral Link".
    - Copy/Share Link.
    - View simple stat: "Total Clicks" / "Total Earnings".

## 3. Out-of-Scope (Deferred to v1.1)
- **Post Ad**: Users must use Web to post.
- **Messaging**: Use Phone/WhatsApp for MVP communication.
- **Payments**: No In-App Purchases (IAP) yet.
- **Dealer Dashboard**: Dealers use Web for management.
- **Profile Edit**: Basic read-only or minimal edit.

## 4. Success Metrics
- **App Store Rating**: > 4.5.
- **Crash Free Users**: > 99%.
- **Retention**: Day-1 Retention > 40%.
