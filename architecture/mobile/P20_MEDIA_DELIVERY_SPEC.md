# P20: Media Delivery Specification

## 1. Overview
Mobile devices have varying screen densities (1x, 2x, 3x) and limited bandwidth. Serving full-resolution desktop images is performance suicide.

## 2. Image Resizing Strategy
Since we are using a self-hosted or standard storage, we need an on-the-fly resizing mechanism or pre-generated sizes.
**MVP Decision**: Use a dynamic resizing proxy or library if available, otherwise enforce **Client-Side Resizing** (upload) and **Thumbnail Generation** (backend).

### 2.1. Thumbnail Generation (Backend)
When an image is uploaded via Web (since Mobile Post Ad is out of scope):
1.  **Original**: Stored as is.
2.  **Mobile-Card**: `400x300` (WebP, Q=80).
3.  **Mobile-Detail**: `800x600` (WebP, Q=85).

### 2.2. URL Structure
The API should return a structured image object, not just a string.
```json
"images": [
  {
    "id": "img-123",
    "original": "https://cdn.com/img-123.jpg",
    "thumbnail": "https://cdn.com/img-123-thumb.webp",
    "medium": "https://cdn.com/img-123-med.webp"
  }
]
```

## 3. Caching Policy
- **CDN**: Cache-Control: `public, max-age=31536000, immutable`.
- **App**: Use `cached_network_image` (Flutter) to store images on device disk to avoid re-downloading.

## 4. Placeholder Strategy
- **BlurHash**: (Optional for v1.1) Send a short string to show a blurred version while loading.
- **Shimmer**: Use skeleton loading (shimmer effect) in the UI while fetching URLs.
