# Real Estate Residential Tree v1

**Rule:** Sorting is **Alphabetical by Localized Name**. The backend/frontend must sort the list dynamically based on the user's language, not by a fixed ID.

## 1. Transaction Types (İşlem Türleri)
These are fixed roots.
1.  **For Sale** (Satılık / Zu Verkaufen / À Vendre)
2.  **For Rent** (Kiralık / Zu Vermieten / À Louer)
3.  **Daily Rental** (Günlük Kiralık / Kurzzeitmiete / Location Saisonnière)

---

## 2. Categories (Alphabetical Sort)

### 🇹🇷 TR - Konut
1.  **Bina** (Building)
2.  **Çiftlik Evi** (Farmhouse)
3.  **Daire** (Apartment)
4.  **Müstakil Ev** (Detached House)
5.  *Residans (Optional)*
6.  *Villa (Optional)*

### 🇩🇪 DE - Wohnen
1.  **Bauernhaus** (Çiftlik Evi)
2.  **Einfamilienhaus** (Müstakil Ev)
3.  **Gebäude** (Bina)
4.  **Residenz** (Residans - Optional)
5.  **Villa** (Villa - Optional)
6.  **Wohnung** (Daire)

### 🇫🇷 FR - Résidentiel
1.  **Appartement** (Daire)
2.  **Bâtiment** (Bina)
3.  **Ferme** (Çiftlik Evi)
4.  **Maison Individuelle** (Müstakil Ev)
5.  **Résidence** (Residans - Optional)
6.  **Villa** (Villa - Optional)

---

## 3. Data Structure Implication
The `Category` table will not determine the order via `sort_order` for these leaves. The UI must:
`categories.sortBy(c => c.translations[currentLang].name)`
