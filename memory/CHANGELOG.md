# CHANGELOG

## Uygulanan Özellikler
- **P107 L0/L1 Alfabetik Sıralama Modu (2026-03-01):** Ana Site Kategorisi paneline L0 (modül) ve L1 için manuel/alfabetik sıralama modu eklendi. Alfabetik modda yukarı/aşağı butonları devre dışı.
- **P106 Kardeş Güncelleme Onayı Kaldırıldı (2026-03-01):** Kademeli hiyerarşide “kardeşlere uygula” onayı kaldırıldı; otomatik klonlama devam eder, güncellemeler yalnız seçili dalı etkiler.
- **P107 Ana Site Kategorisi Tasarım Paneli (2026-03-01):** Admin → Site İç Tasarımı → Ana Site Kategorisi ekranı eklendi; modül ve L1 sırası yukarı/aşağı ile belirleniyor, kolon genişliği ayarlanıyor.
- **P107 Homepage Kategori Kolonu (2026-03-01):** Ana sayfa kategori kolonu artık admin config’ten geliyor; modül/L1 sırası, kolon genişliği ve “Devamını Gör” (ilk 5 L1) davranışı uygulanıyor.
- **P106 Modül/L1 Sıra Zorunluluğu Kaldı (2026-03-01):** Yeni kategori üretiminde sıra numarası zorunluluğu ve çakışma engeli kaldırıldı.
- **P106 Kardeş Mirası (2026-03-01):** Kademeli hiyerarşide Level 1→2’den itibaren kardeş yapı mirası eklendi; ilk kardeşin alt listesi şablon oluyor, yeni kardeşler otomatik klonlanıyor. “Mirası Kopar” override butonu aktif.
- **P106 Modül Kayıt Hatası Netleştirme (2026-03-01):** Kategori oluşturma hatalarında safe JSON parse + HTTP status fallback eklendi; “Modül oluşturulamadı” yerine gerçek hata mesajı görülebilecek.
- **P106 Admin Kategori Kademeli Hiyerarşi Editörü (2026-03-01):** Yeni kategori modalı "level builder" mantığına taşındı: Root modül alanları, Level Navigator (root/back/next), sınırsız seviye kolonları, leaf işaretleme ve drag-sıra. Vasıta modülü için şablon + API/JSON/Excel import paneli eklendi.
- **P106 Test Doğrulama (2026-03-01):** `/app/test_reports/iteration_68.json` ve `auto_frontend_testing_agent` PASS. Leaf işaretlendiğinde "Altını Doldur" butonu gizleniyor (self-test screenshot: `admin_categories_leaf.png`).
- **P105d Standart Emlak Hiyerarşi Seed (2026-03-01):** Backend’e `POST /api/admin/categories/seed/real-estate-standard` endpointi eklendi. Şema otomatik ve idempotent kuruluyor: **L1 Emlak → L2 (Konut, Ticari Alan, Arsa) → L3 (Satılık, Kiralık, Günlük Kiralık) → L4 (Daire, Müstakil Ev, Köşk & Konak, Bina, Çiftlik Evi)**.
- **P105d Home Kategori Görünümü (2026-03-01):** Ana sayfa sol blok L1/L2 kuralına göre filtrelendi; üstte L1, altında bağlı L2 satırları ve yanında ilan adetleri. Sol kolon genişliği daraltılıp kart görsel dili netleştirildi.
- **P105d Admin Hiyerarşi Görünümü (2026-03-01):** Admin kategori ekranına L1→L6 hiyerarşi önizleme paneli eklendi (seviye rozetleri + adet). Üst aksiyona “Standart Emlak Şeması” butonu eklendi.
- **P105d Test Doğrulama (2026-03-01):** `/app/test_reports/iteration_67.json` PASS (**backend 100% / frontend 100%**). Seed endpoint, idempotency, admin hiyerarşi paneli ve home L1/L2 render doğrulandı.
- **P106 Listing Flow (Draft → Preview → Doping → Submit) Canlı (2026-03-01):** Backend’e yeni gerçek akış endpointleri eklendi: `POST /api/v1/listings/vehicle/{id}/preview-ready`, `GET /api/v1/listings/vehicle/{id}/preview`, `GET /api/v1/listings/doping/options`, `POST /api/v1/listings/vehicle/{id}/doping`, `POST /api/v1/listings/vehicle/{id}/submit-review`.
- **P106 State Machine + Idempotency (2026-03-01):** Akış state’leri canlı: `draft -> preview_ready -> doping_selected (opsiyonel) -> submitted_for_review`. `submit-review` endpointinde `Idempotency-Key` zorunlu; aynı key ile tekrar submit duplicate üretmeden aynı sonucu döndürüyor, farklı key ile tekrar deneme `409`.
- **P106 Admin Queue + Audit Eventleri (2026-03-01):** Submit edilen ilanlar admin moderation queue’da `PENDING` olarak görünür. Audit eventleri yazılıyor: `LISTING_PREVIEW_READY`, `LISTING_DOPING_SELECTED`, `LISTING_SUBMITTED_FOR_REVIEW` (metadata: user/listing/draft/category_path/doping_selection/idempotency_key).
- **P106 Frontend Akış Sayfaları (2026-03-01):** `/ilan-ver/detaylar` gerçek draft kaydı + preview-ready doğrulaması ile çalışır hale getirildi. Yeni sayfalar eklendi: `/ilan-ver/onizleme` (backend snapshot), `/ilan-ver/doping` (none/urgent/showcase seçimi). Doping kartı preview ekranında yalnızca doping aktifse gösteriliyor.
- **P106 Test Doğrulama (2026-03-01):** `/app/test_reports/iteration_66.json` ile backend+frontend **%100 PASS**. Ek hızlı UI doğrulaması `auto_frontend_testing_agent` ile tamamlandı.
- **P105c Admin Kategori Liste Sadeleştirme (2026-02-28):** `AdminCategories` liste tablosu root-only moda alındı (`parent_id` dolu alt kategoriler tablo satırı olarak gösterilmiyor). Böylece admin ekran şişmesi engellendi; alt kategori düzeni sadece kategori düzenleme/oluşturma akışı içinde yönetiliyor.
- **P105c Home Kategori Kolonu İnce Ayar (2026-02-28):** Sol blokta modül > ana kategori > 1. seviye alt kategori (adet) standardı korunurken ana kategori satırındaki adet etiketi kaldırıldı; adet gösterimi alt kategori satırlarına odaklandı.
- **P105c /ilan-ver Kategori Kolonları Final (2026-02-28):**
  - Desktop: N-seviye multi-column seçim davranışı korunup deterministik sağ kolon kapanışı doğrulandı.
  - Leaf kuralı: Yalnız leaf seçilince tamam durumu + `Devam` aktif.
  - Lazy load + session cache: child fetch yalnız seçimde; aynı parent tekrarında cache kullanımı.
  - Kolon bazlı hata/retry UI: child fetch fail olduğunda kurumsal hata metni + tekrar dene butonu.
  - Mobil karar uygulandı: stepper (tek kolon), `Geri/İleri`, üstte sabit breadcrumb + seviye etiketi.
- **P105c Test Doğrulama (2026-02-28):** `/app/test_reports/iteration_65.json` frontend doğrulaması **100% PASS** (admin root-only liste, home module-root-L1 görünümü, /ilan-ver desktop+mobile davranışları).
- **P105b Home Sol Blok Standardizasyonu (2026-02-28):** Ana sayfa sol blok `Modül -> Ana Kategori -> 1. Alt Kategori (adet)` hiyerarşisine çekildi. Veri modeli `moduleGroups[]` mantığında normalize edildi (`module_key`, `module_label`, `roots[]`, `children_level1[]`). Limit kuralları eklendi: modül başına ilk 8 root + `Tümünü Göster`, root başına ilk 8 child + `Daha fazla göster`.
- **P105b Vitrin/Acil Veri Akışı + Periyodik Yenileme (2026-02-28):** Home vitrin ilanları `doping_type=showcase` ile, ACİL sayaç `doping_type=urgent` ile okunuyor; fetch döngüsü 5 dakikada bir otomatik yenileme şeklinde çalışıyor.
- **P105b Urgent Seed Doğrulama (2026-02-28):** Admin üzerinden yayındaki ilanlara seed uygulanarak en az 10 acil ilan üretildi (API doğrulaması: `/api/v2/search?doping_type=urgent` toplam 10).
- **P105b Search Doping Chip + SEO Tutarlılığı (2026-02-28):** `SearchPage` üzerinde doping filtre chip’i (`search-doping-chip`) kalıcı/kararlı render olacak şekilde düzeltildi; doping bazlı title/description senkronu eklendi; urgent empty-state kurumsal metne güncellendi.
- **P105 Ana Sayfa HTML Toparlama (2026-02-28):** Home akışı kullanıcı talebine göre sadeleştirildi. Vitrin alanı artık `GET /api/v2/search?...&doping_type=showcase` ile **admin onaylı vitrin** ilanlarını çekiyor; eski placeholder/kalıntı davranışları temizlendi. `ACİL` alanı linke çevrilip `/search?doping=urgent` yönlendirmesi eklendi. Sol kategori blokları admin kategorilerinden `Ana Kategori > 1. Alt Kategori (ilan adedi)` formatında render edildi.
- **P105 Search Doping URL Desteği (2026-02-28):** URL state’e `doping` parametresi eklendi (`useSearchState`). `SearchPage` artık `doping=urgent/showcase` parametresini backend’e `doping_type` olarak iletir ve başlıkları (`Acil İlanlar` / `Vitrin İlanları`) dinamik gösterir.
- **P105 Backend Doping Filtreleme (2026-02-28):** `GET /api/v2/search` endpointine `doping_type` parametresi eklendi. Meili filtre ifadesi `showcase -> is_featured=true`, `urgent -> is_urgent=true` kurallarıyla genişletildi; filterable attribute setine `is_featured/is_urgent` dahil edildi.
- **P105 İlan Ver Route + PDF Uyumlu Detay Şablonu (2026-02-28):** `/ilan-ver` route’u artık aktif ekran (redirect değil), `/ilan-ver/kategori-secimi -> /ilan-ver` redirecti korundu. `ListingDetails` sayfası PDF’e göre 1..8 madde düzeninde yeniden tasarlandı: çekirdek/parametre/adres/detay gruplar/medya/iletişim/kampanya/koşullar + kampanya kartları + koşul checkbox + devam aksiyonu.
- **P105 Test Doğrulama (2026-02-28):** `/app/test_reports/iteration_63.json` PASS (**backend 100%, frontend 100%**). Doğrulanan başlıklar: doping_type API filtreleri, home link yönlendirmeleri, search doping başlıkları, `/ilan-ver` route davranışı ve PDF section yapısı.
- **P104 Admin Render Loop Fix + Kategori Save Stabilizasyon (2026-02-28):** `Layout.js` içinde sidebar section collapse senkron effect’i harden edilerek `Maximum update depth exceeded` döngüsü kapatıldı (state değişmedikçe update yapılmıyor). Sonuç: `/admin/categories` ve ilgili admin rotaları tekrar stabil açılıyor. Kategori hiyerarşi kaydet akışı yeniden doğrulandı; root + child kayıt backend’de başarılı üretildi ve TypeError blokajı tekrar gözlenmedi.
- **P104 Home Showcase Fallback Harden (2026-02-28):** `HomePage` veri yükleme akışı `Promise.all` yerine `Promise.allSettled` yaklaşımına geçirildi. Böylece kategori çağrısı geçici fail olsa bile yayınlanmış showcase layout’u default’a düşmeden uygulanabiliyor; admindeki vitrin ayarlarının yansıma dayanıklılığı artırıldı.
- **P104 Test Doğrulama (2026-02-28):** `/app/test_reports/iteration_62.json` raporunda kritik hedefler PASS: admin kategori ve showcase sayfaları crash olmadan açılıyor, kategori hiyerarşi save akışı çalışıyor, sidebar accordion stabil.
- **P103 Kategori Hata Fix + UI İyileştirmeleri (2026-02-28):** Kullanıcı şikayeti sonrası kategori kayıt akışı tekrar harden edildi. `createCategoryWithSortFallback` artık sadece sıra çakışmasını değil **slug çakışmasını** da otomatik çözerek tekrar dener (örn. `slug-2`), böylece "Ana kategori oluşturulamadı" blokajı azaltıldı. Kategori modalına **Tam Ekran/Normal toggle + resizable panel** eklendi (büyüt/küçült). Grup ve alt kategori kartlarına **drag-drop** sıralama eklendi. Canlı hiyerarşi önizlemesine **Eksik alan var / Tamam** rozetleri eklendi.
- **P103 Batch Publish Dashboard Kartı (2026-02-28):** Admin dashboard’a batch scheduler log/istatistik kartı eklendi (`İşlenen/Yayınlanan/Atlanan/Hata`, son koşular listesi, refresh, manuel "Şimdi Çalıştır"). Backend’e `GET /api/admin/listings/batch-publish/stats` endpoint’i eklendi ve scheduler/manual run sonuçları in-memory recent run listesine yazılıyor.
- **P103 Test Doğrulama (2026-02-28):** `/app/test_reports/iteration_61.json` ile tüm hedefler doğrulandı (**backend 100%, frontend 100%**): kategori modal davranışları (resize/fullscreen/drag-drop/preview badges) ve dashboard batch publish kartı + endpointler PASS.
- **P102 Alt Kategori Grubu Akışı Stabilizasyonu (2026-02-28):** Kullanıcı geri bildirimine göre kategori ekranı tekrar sadeleştirildi ve hatalar giderildi. `Ana Kategori Grupları` metni tamamen kaldırıldı; doğrudan **Alt Kategori** akışı kaldı: `1.1` ile başlar, grup tamamlanınca otomatik `2.1`, sonra `3.1`... şeklinde devam eder. Grup başına alt kartlar yatay/sınırsız (`1.1, 1.2, 1.3 ...`) eklenecek şekilde netleştirildi. Kayıt tarafında da bloklayan hatalar ("alt kategori oluşmadı", "ana kategori oluşturulamadı") için persist akışı group-wrapper yerine çocukları doğrudan parent altına kaydedecek şekilde düzeltildi. Doğrulama: `/app/test_reports/iteration_60.json` (**frontend 100% PASS**, istenen 6/6 davranış doğrulandı).
- **P101 Alt Kategori Akışı Revizyonu (2026-02-28):** Kullanıcı geri bildirimiyle kategori editor tekrar sadeleştirildi: "Ana Kategori Grupları" kaldırıldı, doğrudan **Alt Kategori Grubu** akışı getirildi. Yeni model: grup (1,2,3...) + her grup içinde yatay ve sınırsız altlar (1.1,1.2... / 2.1,2.2...). Grup tamamlandığında otomatik bir sonraki grup taslağı açılıyor (2.1 başlangıcı). Root grup tamamlamak için en az 1 alt kategori zorunlu. Canlı hiyerarşi önizleme ağacı korunarak güncellendi. Doğrulama: `/app/test_reports/iteration_59.json` (**backend 100%, frontend 100% PASS**).
- **P101 Kayıt Hata Azaltma + Boş Sıra Uygulama (2026-02-28):** Kayıt akışındaki "alt kategori/ana kategori oluşturulamadı" şikayetine karşı create akışı güvenli hale getirildi: sıra çakışmasında otomatik uygun sıraya kaydırma, preview endpoint üzerinden `suggested_next_sort_order` ve UI’da tek tık "Uygula".
- **P100 Kategori Akışı Final Düzeltmesi (2026-02-28):** Kullanıcı tarifine göre yeni kategori editörü 2-seviyeli modele kesin geçirildi: **ana grup (1,2,3...)** + seçili grup altında **alt kategoriler (1.1,1.2... / 2.1,2.2...)**. Akış: ana grup seçimi → alt kategori yönetimi; root grup tamamlanınca otomatik sonraki grup taslağı açılıyor. Alt kategori kartları sağa doğru yatay akışta sınırsız ekleniyor. Root tamamlamak için en az 1 alt kategori zorunlu hale getirildi. Ayrıca canlı **hiyerarşi önizleme ağacı** eklendi.
- **P100 Boş Sıra Önerisi (Canlı) (2026-02-28):** `order-index/preview` endpoint’i conflict durumunda `suggested_next_sort_order` döndürür hale geldi; frontend’de sıra input yanında "Önerilen boş sıra" ve tek tık "Uygula" aksiyonu eklendi.
- **P100 Batch Publish Scheduler + Slot Entegrasyonu (2026-02-28):** Kampanya/slot kuralları yayın akışına tam bağlandı. Batch scheduler 5 dakikada bir (`300s`) `pending_moderation` ilanları koşullara göre yayınlar; manuel tetik endpointi eklendi: `POST /api/admin/listings/batch-publish/run`. Slot öncelik kuralı: **Vitrin > Acil > Ücretli > Ücretsiz**. Slot tüketimi publish anında `slot_consumed` olarak işlenir; snapshot listing_type moderasyon publish’te doping alanlarına uygulanır.
- **P99 Kategori Hiyerarşi Akış Revizyonu (2026-02-27):** Kullanıcı akışına göre kategori modalı yeniden akıtıldı: seviye kolonları artık `levelCompletion` kilidine bağlı değil, seçime göre dinamik açılıyor (12 seviyeye kadar). Root kart tamamlandığında sistem otomatik yeni root taslak kartını (Kategori 2, 3, 4 …) ekliyor; böylece `1 -> 1.1/1.2 ... -> 2 -> 2.1 ...` işleyişi destekleniyor. Ayrıca sıra çakışmasında canlı **önerilen boş sıra** (`suggested_next_sort_order`) backend’den dönüyor ve input yanında “Uygula” ile tek tık atanıyor.
- **P99 Kampanya/Slot Kurallarını Yayın Akışına Bağlama (2026-02-27):** Kampanya item seçiminde öncelik kuralı kodlandı: **Vitrin > Acil > Ücretli > Ücretsiz**. Campaign slot tüketimi yayın akışına bağlandı (`slot_consumed`, `slot_consumed_at`) ve kota doluysa publish zinciri 409 ile korunuyor. Moderasyon publish adımında pricing snapshot’taki `listing_type` listing doping alanlarına uygulanıyor (`featured_until/urgent_until/paid_until`) ve publish süresi `publish_days` üzerinden set ediliyor.
- **P98 Kategori Oluşturma Hata Düzeltmesi (2026-02-27):** Tüm modüllerde kategori oluşturma akışındaki blokaj giderildi. Frontend `AdminCategories` tarafında hata ayrıştırma iyileştirildi (`detail` array/string/object), `ORDER_INDEX_ALREADY_USED` durumunda otomatik uygun sıra bulup tekrar create eden fallback eklendi (ana kategori + alt kategori). Backend `POST /api/admin/categories` endpointi de harden edildi: sort çakışmasında artık create isteğini düşürmek yerine `_next_category_sort_order` ile bir sonraki uygun `sort_order` otomatik atanıyor. Sonuç: kullanıcı `1` gibi çakışan sıra verse dahi kategori oluşturma akışı kesilmeden devam ediyor.
- **P97 Timeline Uzatma + Uyarı İyileştirmesi (2026-02-27):** Kapanış öncesi istenen bağlama/iyileştirme kapsamında `Acil/Vitrin/Ücretli` timeline alanına operasyonel hızlandırıcılar eklendi. `AdminListings` içinde kalan gün <= 3 olduğunda `Kalan` değeri kırmızı uyarı (`text-rose-600`) ile vurgulanıyor. Ayrıca her satıra `+7g Uzat` ve `+30g Uzat` aksiyonları eklendi; bu aksiyonlar mevcut doping tipini koruyarak `POST /api/admin/listings/{id}/doping` endpointine `until_at` gönderip süreyi ileri taşıyor. Acil yeni pencere davranışı bozulmadan korundu. Doğrulama: `/app/test_reports/iteration_55.json` (**backend 12/12 PASS, frontend 100% PASS**).
- **P96 Doping Timeline Kolonları + Onaylı Acil Yeni Pencere (2026-02-27):** Kullanıcı talebine göre `Acil/Vitrin/Ücretli` sayfalarına (bireysel + kurumsal) yeni kolon eklendi: **Onay Tarihi + Bitiş Tarihi + Kalan Gün**. `AdminListings` içinde `showDopingTimeline = applicationsMode && dopingType in [urgent, showcase, paid]` kuralıyla kolon aktifleşiyor; satırda `published_at`, ilgili doping bitiş alanı (`urgent_until/featured_until/paid_until`) ve kalan gün hesaplaması gösteriliyor. Backend `GET /api/admin/listings` yanıtına `published_at` dahil edildi. Ayrıca `Acil` aksiyonu için yeni pencere akışı finalize edildi: bireysel/kurumsal başvuru ekranlarında `Acil` tıklandığında yeni pencerede ilgili urgent sayfa açılıyor; urgent route’lar `initialStatus="published"` ile yalnızca onaylı acil ilanları listeliyor. Test: `/app/test_reports/iteration_54.json` (**backend 9/9 PASS, frontend 100% PASS**).
- **P95 Onaylı Acil İlanlar Yeni Pencere Akışı (2026-02-27):** Kullanıcı talebine göre `İlan & Moderasyon > Bireysel İlan Başvuruları` ve `Kurumsal İlan Başvuruları` içindeki **Acil** tıklaması yeni pencerede onaylı acil ilan listesine yönlendirildi. `AdminListings` bileşenine `initialStatus` eklendi; route bazında urgent sayfalar `initialStatus="published"` + `initialDopingType="urgent"` ile çalışır hale getirildi (`BackofficePortalApp`). Ayrıca sidebar’daki `Bireysel Acil İlan` ve `Kurumsal Acil İlan` linkleri `_blank` olarak açılıyor. Doğrulama: popup URL `.../individual-listing-applications/urgent`, popup başlığı `Bireysel Onaylı Acil İlanlar`, sidebar urgent link `target=_blank` smoke PASS.
- **P94 Vitrin Senkron + Versiyon Silme (2026-02-27):** Kullanıcı geri bildirimi üzerine vitrin ayarlarının public’e yansımama/kesik senkron problemi kapatıldı. `GET /api/site/showcase-layout` cache header’ı `no-store` yapıldı; public `HomePage` grid kolon uygulaması class-based modele taşındı (`home-v2-showcase-grid-cols-{n}` / `home-v2-category-showcase-grid-cols-{n}`), böylece admindeki **1. Ana Sayfa Vitrin** sütun değeri HTML render’a doğrudan uygulanıyor. Ayrıca versiyon listesine satır bazlı `Sil` butonu eklendi (v11/v10 alanı): draft silme aktif, published için UI disabled + backend guard `400 Aktif versiyon silinemez`. Doğrulama: `/app/test_reports/iteration_53.json` (**backend 9/9 PASS, frontend 100% PASS**).
- **P93 Ana Sayfa Vitrin HTML Bağlantısı Netleştirme (2026-02-27):** Kullanıcı talebine göre public `HomePage` vitrini, Admin > Site İç Tasarım > Vitrin Yönetimi > **1. Ana Sayfa Vitrin** ayarlarından beslenecek şekilde netleştirildi. Vitrin HTML/JSX bloğunda kolon/satır/ilan alanı konfigürasyonuna bağlı render korunurken, responsive tarafta sabit kolon override’ları kaldırıldı; böylece admin’de verilen sütun düzeni doğrudan vitrin gridine uygulanıyor. `GET /api/site/showcase-layout` → `HomePage` entegrasyonu aktif doğrulandı (smoke test).
- **P92 Site İç Tasarım > Vitrin Yönetimi (2026-02-27):** Kullanıcı talebine göre Admin > Site İç Tasarım altında yeni **Vitrin Yönetimi** alanı eklendi (`/admin/site-design/showcase`). Ekranda iki ana bölüm var: **(1) Ana Sayfa Vitrin** ve **(2) Ana Kategori Vitrin**. Her bölümde satır/sütun/ilan alanı manuel yönetiliyor; kategori vitrininde birden fazla ana kategori için ayrı düzen tanımlanabiliyor (kategori bazlı rows/columns/listing_count + aktif/pasif). Taslak kaydet, yayınla, versiyon listeleme/yükleme akışları eklendi.
- **P92 Public Render Bağlantısı + Validation Sertleştirme (2026-02-27):** Public tarafta `HomePage` artık `GET /api/site/showcase-layout` ile yayınlanmış ayarı okuyup ana vitrin kolon/sayısını ve kategori vitrin bloklarını bu konfigürasyona göre render ediyor. Backend’de yeni model ve endpoint seti eklendi: `SiteShowcaseLayout`, `GET /api/site/showcase-layout`, `GET /api/admin/site/showcase-layout`, `GET /api/admin/site/showcase-layout/configs`, `GET /api/admin/site/showcase-layout/config/{id}`, `PUT /api/admin/site/showcase-layout/config`, `POST /api/admin/site/showcase-layout/config/{id}/publish`. Düşük öncelikli test bulgusu da kapatıldı: kategori satırında boş `category_id/category_slug` artık 400 validation hatası döndürüyor.
- **P91 Başvurular için Hızlı Vitrin/Acil Butonları (2026-02-27):** Kullanıcı talebiyle Admin > İlan & Moderasyon altındaki **Bireysel/Kurumsal İlan Başvuruları** satır aksiyonlarına hızlı atama eklendi. `AdminListings` içinde `applicationsMode` + `doping_type in {free, paid}` koşulunda yeni alan gösteriliyor: manuel `Gün` inputu + tek tık `Vitrine Ata` / `Acile Ata` butonları. Aksiyonlar `POST /api/admin/listings/{id}/doping` endpointine `duration_days` ile gönderiliyor, geçersiz günlerde (`0/boş/negatif`) kullanıcıya uyarı veriliyor. Promosyon sonrası ilan artık free/paid olmadığı için hızlı alan gizleniyor (beklenen davranış). Doğrulama: `/app/test_reports/iteration_51.json` (**frontend 100% PASS**).
- **P90 Ücretli Tipi + Kampanya Tip Genişletmesi (2026-02-27):** Kullanıcı onayıyla başvuru ve kampanya akışına `paid` tipi eklendi. `AdminListings` doping sekmeleri `Tümü/Ücretsiz/Ücretli/Vitrin/Acil` olacak şekilde genişletildi; backend `doping_type` filtreleri ve `doping_counts` yapısı `paid` tipini kapsayacak şekilde güncellendi. `POST /api/admin/listings/{id}/doping` artık `paid` kabul ediyor ve `paid_until` alanını yönetiyor. Yeni admin rotaları eklendi: `/admin/listings/paid`, `/admin/individual-listing-applications/paid`, `/admin/corporate-listing-applications/paid` (sidebar + RBAC dahil). Kampanya yönetiminde (`AdminPricingTiers`, `AdminPricingPackages`) kampanya ekle modalına tek-seçim `listing_type` (Ücretsiz/Ücretli/Acil/Vitrin) alanı eklendi; tabloda tip kolonu ve tip bazlı toplam ilan adedi özetleri eklendi. Backend `pricing_campaign_items` modeli/CRUD akışı `listing_type` ile genişletildi, aynı scope+i̇lan tipi için çakışma kontrolü korundu, migration `p70_paid_listing_and_campaign_type.py` eklendi. Doğrulama: `/app/test_reports/iteration_50.json` (**backend 15/15 PASS, frontend PASS**).
- **P89 Doping Navigasyon + Badge Finalizasyonu (2026-02-27):** Admin Listings akışında doping görünürlüğü ve direkt navigasyon tamamlandı. `AdminListings` üzerinde badge davranışı netleştirildi: aktif state’de yalnızca ilgili rozetler (`Vitrin`/`Acil`), aktif değilse `Ücretsiz` etiketi gösteriliyor; bucket metinleri TR etiketlere map edildi. Backoffice route ağı genişletildi: `/admin/listings/featured`, `/admin/listings/urgent`, `/admin/individual-listing-applications/featured|urgent`, `/admin/corporate-listing-applications/featured|urgent`. Sidebar ve RBAC route desenleri bu yeni path’lerle hizalandı (`Layout.js`, `adminRbac.js`). Hydration teknik borcu için `CorporateDashboardDesigner` içinde `largeScreen` başlangıç state’i SSR-safe hale getirildi (window erişimi mount sonrası). Doğrulama: `/app/test_reports/iteration_49.json` (backend 10/10 PASS, frontend PASS, hydration warning yok).
- **P88 Doping Sistemi + Başvuru Ayrıştırma (2026-02-27):** İlan & Moderasyon kapsamı kullanıcı talebine göre güncellendi. Backend’de `listings` için `featured_until` ve `urgent_until` alanları eklendi (model + startup schema ensure + migration dosyası: `p69_listing_doping_columns.py`). Admin listeleme API’sine `applicant_type` (`individual/corporate`) ve `doping_type` (`free/showcase/urgent`) filtreleri eklendi; response’a `doping_counts`, `is_featured`, `is_urgent`, `doping_type` alanları dahil edildi. Moderatör için manuel doping endpointi eklendi: `POST /api/admin/listings/{listing_id}/doping` (7/30/90 + manuel gün). Meilisearch dokümanına `is_featured/is_urgent/featured_until/urgent_until` alanları eklendi; filterable + sortable attribute güncellemesi eklendi ve ranking önceliği `Vitrin > Acil > Ücretsiz` olarak normalize edildi. Frontend’de `Bireysel İlan Başvuruları` ve `Kurumsal İlan Başvuruları` sayfaları 3 sekmeli yapıya geçirildi (Ücretsiz/Vitrin/Acil) ve satır bazlı doping kontrol editörü eklendi. Public Search ve Home vitrin kartlarına `is_featured/is_urgent` badge+border görselleştirmesi eklendi. Test: `/app/test_reports/iteration_47.json` (PASS) + ek self-testlerle doping endpoint doğrulandı.
- **P87 Ana Giriş Sayfası HTML Entegrasyonu (2026-02-27):** Kullanıcının verdiği HTML tasarım referansı React ana giriş sayfasına entegre edildi (`/`). Yeni Home v2: sol panelde ACİL etiketi + kategori arama + ana kategori/ilk alt kategori şablonu, sağ panelde 63 kutuluk vitrin gridi (9x7), üst/orta reklam slotları (`AD_HOME_TOP`, `AD_LOGIN_1`) ve 5 dakikalık vitrin yenileme. Veri kaynakları canlı endpointlerden bağlandı (`/api/categories`, `/api/v2/search`). Kapsamda tüm kritik etkileşim/bilgi alanlarına `data-testid` eklendi. Test: `/app/test_reports/iteration_46.json` (frontend PASS).
- **P86 Kurumsal Header 3. Satır Finali (2026-02-27):** Örnek görsellere göre row3 düzeni finalize edildi. Sol tarafa kullanıcı bloğu (avatar + isim) taşındı; sağ tarafta aksiyon sırası `Mağaza Filtresi → Sayfayı Düzenle/Düzenlemeyi Bitir → Duyurular` olacak şekilde güncellendi. Mağaza filtresi backend’de yetkili kullanıcı listesiyle beslenecek şekilde genişletildi (`/api/dealer/portal/config > header_row3_controls.stores` artık `Tümü + authorized_user` içeriyor). Row3 kontrollerine `page_edit_enabled`, `announcements_enabled`, `user_display_name` alanları eklendi. Dealer overview içindeki mükerrer `Sayfayı Düzenle/Duyurular` butonları kaldırılarak tek kontrol noktası row3 oldu. Doğrulama: `/app/test_reports/iteration_45.json` (backend 9/9 PASS, frontend PASS).
- **P85 P2 HTML Tarafı Geçişi (2026-02-27):** Alerting için HTML rapor katmanı eklendi. Yeni endpoint: `GET /api/admin/ui/configs/{config_type}/ops-alerts/html-report` (`channels` + `window` query desteği, text/html çıktı). Admin Publish Health UI’da `HTML Rapor Aç` aksiyonu eklendi ve seçili kanal parametresiyle yeni sekmede rapor açar hale getirildi. Regression korunumu ve auth kontrolleri test edildi. Test: `/app/test_reports/iteration_44.json` (backend 9/9 PASS, frontend PASS).
- **P84 P2 Toplu Kapanış (2026-02-27):** Alerting tarafında kanal-bazlı operasyon modeli tamamlandı. Backend’de `ops-alerts` endpointleri `channels` parametresi ile modül bazlı çalışacak şekilde genişletildi (`secret-presence`, `rerun-simulation`, `delivery-audit`) ve yeni `GET /api/admin/ui/configs/{config_type}/ops-alerts/secret-checklist` endpointi eklendi. Dry-run sırası SMTP→Slack→PagerDuty olarak kanıtlandı (correlation/audit kayıtları). Legacy publish cleanup kapsamında `POST /api/admin/ui/configs/{config_type}/publish/{config_id}` ile `GET /api/admin/ui/configs/{config_type}/legacy-usage` fiziksel olarak kaldırıldı (404). UI teknik borçta DealerLayout mağaza filtresi ve AdminCategories liste filtreleri `<select>`ten buton/dropdown yapısına taşındı. Kanıt dokümanları: `/app/docs/P2_ALERTING_SECRET_CHECKLIST.md`, `/app/docs/P2_ALERTING_DRY_RUN_SCENARY.md`, `/app/docs/P2_ALERTING_MODULE_CLOSURE_REPORT.md`, `/app/docs/P2_UI_AND_LEGACY_CLEANUP_REPORT.md`. Test: `/app/test_reports/iteration_43.json` (backend 23/23 PASS, frontend PASS).
- **P83 P0 Toplu Kapanış (2026-02-27):** Corporate dashboard modülleri için canlı veri + empty-state stratejisi tek turda kapatıldı. `GET /api/dealer/dashboard/summary` endpointinde sabit package fallback kaldırıldı, `demand_customer_count` ve `matching_listing_count` gerçek `Conversation/Listing` query’lerinden hesaplanır hale getirildi. `GET /api/dealer/reports` endpointinde package adı fallback’i kaldırıldı (plan/invoice yoksa null + empty-state). `GET /api/dealer/dashboard/metrics` subscription alanı gerçek son invoice/plan verisiyle dolduruldu. Dealer listings UI’da hardcoded `0` metrikleri kaldırılıp backend kaynaklı alanlar (yoksa `-`) gösterimine geçildi. Kapanış testi: `/app/test_reports/iteration_42.json`.
- **P82 P1 Alt Modül Kapanışı (2026-02-27):** P1 kapsamı tek iterasyonda kapatıldı. Dealer `Hesabım` sayfası `?section=` deep-link destekli hale getirildi (`profile/address/security/notifications/blocked`) ve backend’de yeni endpointler eklendi: `POST /api/dealer/settings/change-password`, `GET/PATCH /api/dealer/settings/preferences`, `POST/DELETE /api/dealer/settings/blocked-accounts`. Admin Kategoriler listesine `Görselli/Görselsiz` filtresi ve görünür kayıt sayacı eklendi; kategori görsel alanında format + son güncelleme metadata gösterimi tamamlandı. Doğrulama: `/app/test_reports/iteration_41.json` (backend 16/16 PASS, frontend PASS).
- **P81 Kategori Listesi Görsel Kolonu (2026-02-27):** Admin > Kategoriler liste tablosuna `Görsel` kolonu eklendi. Satırlarda `image_url` varsa thumbnail preview, yoksa placeholder gösterimi eklendi; cache-bust için `updated_at` tabanlı URL parametresi kullanıldı. Böylece ana kategori görselleri listede hızlı doğrulanabilir hale geldi. Test: admin categories smoke screenshot (`/tmp/admin-categories-list-image-column.png`) + data-testid doğrulaması.
- **P80 Admin Kategori Ana Görsel Alanı (2026-02-27):** Admin > Kategoriler > Yeni Kategori/Düzenle akışına yalnızca **ana kategori (root)** için görsel yükleme alanı eklendi. Frontend’de upload+preview (png/jpg/webp, 2MB, center-crop bilgilendirmesi), `Kaldır/Değiştir`, root-dışı durumda kilitli mesajı ve zorunlu validasyon eklendi. Backend’de `POST /api/admin/categories/image-upload` endpointi eklendi (2MB limit, format doğrulama, 1:1 center-crop, `/api/site/assets/categories/...`), `CategoryCreatePayload/CategoryUpdatePayload` için `image_url` desteği açıldı ve child category için `CATEGORY_IMAGE_ROOT_ONLY` kuralı enforce edildi. Test: `/app/test_reports/iteration_40.json` (PASS).
- **P79 Satın Al + Hesabım İyileştirme (2026-02-27):** Sıralama korunarak `Satın Al` ve `Hesabım` ekranları iyileştirildi. `/dealer/purchase` sayfası paket kataloğu + fatura özet kartları + backend uyumlu durum filtreleri (`all/issued/paid/void/refunded/draft`) + ödenebilir fatura için checkout aksiyonu ile güncellendi. `/dealer/settings` sayfası `Hesap Bilgilerim`/`İşletme Bilgileri` sekmeli, etiketli alanlar ve doğrulama (şirket adı + e-posta formatı) ile yeniden düzenlendi. Ödeme başarı/iptal dönüş linkleri satın alma ekranına yönlendirildi. Test: `/app/test_reports/iteration_39.json` (PASS, low issue fix uygulandı).
- **P78 Danışman Takibi PDF Hizalama (2026-02-27):** Sıralama korunarak `Danışman Takibi` ekranı eklendi (`/dealer/consultant-tracking`). Backend `GET /api/dealer/consultant-tracking` endpointi oluşturuldu (consultants/evaluations/summary + sort_by). Frontend’de danışman kartları, gelişmiş sıralama, değerlendirme tabı ve tablo eklendi. Test agent tarafından consultant endpoint 500 hatası fixlenerek stabil hale getirildi (company_name kaynağı DealerProfile). Kanıt: `/app/docs/P1_DEALER_CONSULTANT_TRACKING_ALIGNMENT_EVIDENCE.md`, test: `/app/test_reports/iteration_38.json`.
- **P77 Favoriler + Raporlar PDF Hizalama (2026-02-27):** Sıralama korunarak `Favoriler` ve `Raporlar` ekranları tamamlandı. `GET /api/dealer/favorites` endpointi eklendi (favorite_listings/searches/sellers + summary); `/dealer/favorites` sayfasında 3 tab + arama + tablo yapısı kuruldu. `GET /api/dealer/reports` endpointi genişletildi (window_days 7/14/30/90, report_sections, package_reports, doping_usage_report) ve `/dealer/reports` sayfasında bölüm tabları + dönem filtresi + metrik/seri görünümleri eklendi. `Sanal Turlar` menüde yok durumu korundu. Kanıt: `/app/docs/P1_DEALER_FAVORITES_REPORTS_ALIGNMENT_EVIDENCE.md`, test: `/app/test_reports/iteration_37.json`.
- **P76 Mesaj Okundu + Müşteri Yönetimi PDF Hizalama (2026-02-27):** Mesajlar ekranına okundu bilgisi eklendi: `Okunma` kolonu, `Okundu/Okunmadı` badge, `Okundu İşaretle` aksiyonu. Backend `GET /api/dealer/messages` yanıtı `unread_count/read_status` ve `summary.unread_listing_messages` ile genişletildi; `POST /api/dealer/messages/{conversation_id}/read` eklendi. Sıralı ilerlemede `Müşteri Yönetimi` ekranı da PDF’e göre dolduruldu: `Kullanıcı Listesi` / `Mağaza Kullanıcısı Olmayanlar` tabları, Ad Soyad/E-Posta/Durumu filtreleri, tablo kolonları (Ad Soyad, E-Posta, Durumu, İşlemler). Kanıt: `/app/docs/P1_DEALER_MESSAGES_READ_AND_CUSTOMERS_ALIGNMENT_EVIDENCE.md`, test: `/app/test_reports/iteration_36.json`.
- **P75 Mesajlar Menüsü PDF Hizalama (2026-02-27):** Sıralı akışta `Mesajlar` ekranı PDF’e göre dolduruldu. Başlık/sayaç (`İlan Mesajlarım (x)`), iki tab (`Yayında Olan İlanlar`, `Bilgilendirmeler`), arama + filtre aksiyonu, listing tablosu ve bilgilendirme tablosu eklendi. Backend `GET /api/dealer/messages` endpointi `notification_items` ve `summary` alanlarıyla genişletildi. Kanıt: `/app/docs/P1_DEALER_MESSAGES_PDF_ALIGNMENT_EVIDENCE.md`.
- **P74 İlanlar Menüsü + Sanal Turlar Kaldırma (2026-02-27):** Row2 ana menüden `Sanal Turlar` kaldırıldı (Avrupa kapsamı). `İlanlar` sayfası PDF sırasına göre dolduruldu: başlık, arama, durum tabları (Yayında/Yayında Değil/Tümü), tablo/kart yapısı, satır aksiyonları (`Yayına Al`, `Arşivle`) ve durum/filtre akışları. Kanıt: `/app/docs/P1_DEALER_LISTINGS_PDF_ALIGNMENT_EVIDENCE.md`.
- **P73 Özet Menüsü PDF Hizalama (2026-02-27):** `Özet` menüsü tıklanınca içerik PDF’e göre dolduruldu. Dealer overview sayfasında Mağaza Performansı (24s/7g ziyaret), ilan ziyaret kırılım tablosu, paket durumu (kullanılan/kalan), yayındaki ilan/müşteri talep KPI kartları ve veri uyarı alanı eklendi. Özet içindeki kartlardan ilgili sayfalara (Raporlar, İlanlar, Müşteriler, Satın Al) dolaşım aktif. Backend summary endpointi `overview` bloğu ile genişletildi. Evidence: `/app/docs/P1_DEALER_OVERVIEW_PDF_ALIGNMENT_EVIDENCE.md`.
- **P72 Kurumsal Menü Satır Yapısı (2026-02-27):** Dealer sayfasında menü yerleşimi güncellendi: sol dikey sidebar kaldırıldı, ana menü 2. satıra yatay alındı. 1. satır kurumsal header korunarak bırakıldı. 2. satır menü öğeleri (`Özet, İlanlar, Sanal Turlar, Mesajlar, Müşteri Yönetimi, Favoriler, Raporlar, Danışman Takibi, Satın Al, Hesabım`) tıklama ile aşağı açılan alt menü paneli davranışına geçirildi. PDF hiyerarşisindeki alt menüler row2 altında render ediliyor. Metin kontrastı güçlendirildi; silik görünüm giderildi.
- **P71 Kurumsal Menü Accordion + Kontrast (2026-02-27):** Dealer sol menüde uzun hiyerarşi için açılır/kapanır accordion davranışı eklendi. Üst/alt menüler artık tıklanınca aşağı açılıyor; varsayılan olarak sadece gerekli dal açık. `Favoriler` toggle bug’ı düzeltildi (expand/collapse çift yönlü çalışıyor). Menü metin kontrastı artırıldı (`text-slate-900`, aktif durumda `bg-slate-800 text-white`) ve sidebar liste alanı `max-height + overflow-y-auto` ile taşma kontrolüne alındı.
- **P70 Kurumsal Menü Yapısı PDF Hizalama (2026-02-27):** Dealer portal sol menüsü (`DealerLayout`) PDF’teki kurumsal hiyerarşiye göre güncellendi. Menü ağacı artık `Ofisim` kökü altında çok seviyeli olarak render ediliyor: Özet, İlanlar, Sanal Turlar, Mesajlar, Müşteri Yönetimi>Sözleşmeler, Favoriler alt kırılımları, Raporlar alt kırılımları, Danışman Takibi, Satın Al, Hesabım ve alt başlıkları. Mevcut canlı route’lar (`/dealer/overview`, `/dealer/listings`, `/dealer/messages`, `/dealer/customers`, `/dealer/reports`, `/dealer/purchase`, `/dealer/settings`, `/dealer/company`, `/dealer/invoices`) menü düğümlerine eşlendi; `data-testid` kapsamı eklendi. Kaynak: `kurumsal (ticari) dashboard.pdf`.
- **P69 Ops Publish Health + Alert Reliability (2026-02-27):** Yeni endpointler: `GET /api/admin/ops/alert-delivery-metrics?window=24h` (server-side success-rate KPI + channel breakdown), `POST /api/admin/ops/alert-delivery/rerun-simulation` (Admin/Ops yetkisi, dakika başı 3 rate-limit, `OPS_ALERT_SIMULATION_TRIGGERED` audit metadata). `/admin/ops/publish-health` sayfası eklendi: 24s başarı oranı kartı, Slack/SMTP/PagerDuty mini breakdown, son failure timestamp, tek tık re-run, canlı sonuç/fail-fast görünümü, publish KPI özeti. Mobile overflow (390px) düzeltildi. Index migration: `p68_ops_alert_delivery_index.py`. Evidence: `/app/docs/P1_OPS_PUBLISH_HEALTH_ALERT_RELIABILITY_EVIDENCE.md`, KPI doc update: `/app/docs/PUBLISH_KPI_DEFINITION_V1.md`, testler: `/app/test_reports/iteration_35.json`, `37 passed, 2 skipped`.
- **P68 Ops Alert Channel Integration Verify (2026-02-27):** `GET /api/admin/ui/configs/{config_type}/ops-alerts/secret-presence` endpointi eklendi (kanal bazlı ENABLED/DISABLED + missing key listesi). `POST /ops-alerts/simulate` gerçek kanal doğrulama akışını destekleyecek şekilde genişletildi: correlation_id, fail-fast blokaj çıktısı, kanal bazlı sonuç şeması (Slack/SMTP/PagerDuty), retry/backoff log alanları ve masked telemetry. `GET /ops-alerts/delivery-audit` endpointi eklendi (correlation_id filtreli audit doğrulama). Bu ortamda secret’lar eksik olduğu için akış güvenli şekilde **Blocked: Missing Secrets** olarak doğrulandı. Evidence: `/app/docs/OPS_ALERTS_CHANNEL_INTEGRATION_P0_EVIDENCE.md`, test: `/app/test_reports/iteration_34.json`.
- **P67 Operasyonel Stabilizasyon + P2 Temizlik (2026-02-27):** Ops hardening tamamlandı. Yeni endpointler: `/ops-thresholds`, `/ops-alerts/simulate`, `/legacy-usage`; publish audit endpoint KPI/telemetry/windows/trends döndürecek şekilde genişletildi (1h/24h/7d, conflict_rate, p95 duration, retry medyan vb). Corporate Dashboard’da Publish Audit kartı KPI + sparkline trend + alert badge ile güçlendirildi. **Legacy publish endpoint** hard-removed davranışına alındı (`410 LEGACY_ENDPOINT_REMOVED`, deprecation headers). Tek publish kontratı yeni endpointte bırakıldı. Dokümanlar: `/app/docs/PUBLISH_OPS_THRESHOLD_V1.md`, `/app/docs/PUBLISH_KPI_DEFINITION_V1.md`, `/app/docs/LEGACY_PUBLISH_DEPRECATION_PLAN.md`. Evidence: `/app/docs/OPS_HARDENING_P2_CLEANUP_EVIDENCE.md`, test raporu: `/app/test_reports/iteration_33.json`.
- **P66 Conflict UX + Deterministic Publish Telemetry (2026-02-27):** Conflict dialog tek aksiyonlu senkronizasyona geçirildi: **Latest Draft’ı Çek + Diff’i Yeniden Aç**. Bu aksiyon latest draft’ı server’dan çekip local state’i replace ediyor ve publish dialogunu otomatik yeniden açıyor. Hash tabanlı drift guard eklendi (`local_hash` vs `server_hash`); mismatch durumunda publish butonu disable. Backend’de `resolved_config_hash` publish öncesi doğrulanıyor (`409 CONFIG_HASH_MISMATCH`). Yeni endpointler: `/api/admin/ui/configs/{config_type}/conflict-sync` ve `/api/admin/ui/configs/{config_type}/publish-audits`. Audit/telemetry genişletmesi: `DRAFT_UPDATED`, `DRAFT_SYNCED_AFTER_CONFLICT`, `ui_config_publish_attempt` eventleri; metadata alanları `conflict_detected`, `lock_wait_ms`, `retry_count`, `publish_duration_ms`. Admin UI’da Publish Audit kartı (conflict badge + retry + lock süreleri + telemetry metrikleri) eklendi. Evidence: `/app/docs/UI_CONFLICT_UX_PUBLISH_TELEMETRY_P0_EVIDENCE.md`, test raporu: `/app/test_reports/iteration_32.json`.
- **P65 Header + Theme P0 Simplification (2026-02-27):** Faz 1+2 tamamlandı. Header mimarisi `global + dealer override` modeline sadeleştirildi; bireysel header editörü UI’dan kaldırıldı ve backend admin endpointleri `403 FEATURE_DISABLED` ile hard-close edildi. Corporate header effective erişimi dealer scope zorunlu (`403 UNAUTHORIZED_SCOPE`). Header publish snapshot alanları zorunlu scope-aware hale getirildi: `owner_type`, `owner_id`, `config_version`, `resolved_config_hash`; scope mismatch `409 SCOPE_CONFLICT`. Theme override modeli `Dealer Override > Global Theme` olarak sabitlendi; `user` scope assignment `400 INVALID_THEME_SCOPE`; resolved theme snapshot/hash çıktılarına eklendi. Dokümanlar: `/app/docs/HEADER_ARCHITECTURE_V2.md`, `/app/docs/THEME_OVERRIDE_MODEL_V2.md`. Evidence: `/app/docs/HEADER_THEME_P0_EVIDENCE.md`, test raporu: `/app/test_reports/iteration_31.json`.
- **P64 Publish Hardening P0 (2026-02-27):** Publish güvenliği sertleştirildi. `config_version` hem yeni (`/api/admin/ui/configs/{config_type}/publish`) hem legacy (`/api/admin/ui/configs/{config_type}/publish/{config_id}`) endpointte zorunlu hale geldi. Eksik versiyon: `400 MISSING_CONFIG_VERSION`; mismatch: `409 CONFIG_VERSION_CONFLICT` (contract fields: `current_version`, `your_version`, `last_published_by`, `last_published_at`). Kısa publish lock (`PUBLISH_LOCKED`) eklendi. Dashboard publish dialogu görsel diff (Önceki/Yeni Grid + highlight) ile zorunlu kontrol adımına taşındı. Rollback reason zorunlu oldu (`400 MISSING_ROLLBACK_REASON`) ve audit metadata’ya reason yazılıyor. UI’da conflict modal (reload + diff) ve “Son Snapshot’a Dön” hızlı aksiyonu eklendi. Legacy endpoint deprecated işaretlendi (remove plan: P2). Evidence: `/app/docs/UI_PUBLISH_HARDENING_P0_EVIDENCE.md`, test: `/app/test_reports/iteration_30.json`.
- **P63 Logo Upload P0 Stabilizasyon (2026-02-26):** Kurumsal header logo upload hattı kontrat bazlı error_code ile sertleştirildi (`INVALID_FILE_TYPE`, `FILE_TOO_LARGE`, `INVALID_ASPECT_RATIO`, `INVALID_FILE_CONTENT`, `STORAGE_PIPELINE_ERROR`). UI’da inline error banner (özet + beklenen/gelen detay + kod) eklendi; sessiz hata hissi kapatıldı. Upload başarı yanıtına `storage_health` eklendi ve `GET /api/admin/ui/logo-assets/health` endpointi açıldı. Preview URL cache-bust (`?v=timestamp`) ile güncellendi. RBAC/scope doğrulaması tamamlandı (dealer 403, system+scope_id normalize). Publish sonrası dealer canlı header logo görünümü doğrulandı. Test kanıtı: `/app/test_reports/iteration_29.json`, evidence: `/app/docs/LOGO_UPLOAD_P0_STABILIZATION_EVIDENCE.md`.
- **P62 Dealer Dashboard V2 P1 Frontend Entegrasyon (2026-02-26):** Admin UI Designer V2’ye **Kurumsal Dashboard V2** tabı eklendi (dnd-kit ile 12 kolon grid, widget palette: KPI/Grafik/Liste/Paket Özeti/Doping Özeti, draft autosave, publish öncesi diff + zorunlu onay modalı, rollback seçimli akış). **Bireysel Header** tabı row bazlı DnD + visible toggle + logo fallback ile yeniden tasarlandı; draft/publish/rollback endpointleriyle entegre edildi. Backend’de `/api/admin/ui/configs/{type}/diff`, `/publish` (require_confirm), `/rollback` endpointleri ve publish/rollback audit log yazımı tamamlandı. Dealer canlı dashboard ekranı config-driven render’a geçirildi (`/api/ui/dashboard`). Test kanıtı: `/app/test_reports/iteration_28.json` (backend+frontend PASS), self-test: `13/13 PASS`, evidence: `/app/docs/DEALER_DASHBOARD_V2_FRONTEND_EVIDENCE.md`.
- **P61 Dealer Dashboard V2 P0 Backend-Only (2026-02-26):** `ui_configs` tablosuna `layout/widgets` JSONB kolonları (`p61_ui_dashboard_cfg`) eklendi; `UIConfig` modeli ve `ui_designer_routes` dashboard akışı bu alanları native yönetir hale getirildi. Save/publish aşamasında backend guardrail enforce: **min 1 KPI**, **max 12 widget**, widget/layout `widget_id` benzersizlik + eşleşme kontrolü. `/api/admin/ui/configs/dashboard` ve `/api/ui/dashboard` yanıtları layout/widgets ile genişletildi. Migration upgrade+downgrade+re-upgrade doğrulandı. Test kanıtı: `/app/test_reports/iteration_27.json` (PASS, backend 10/10).
- **P59 UI Designer Foundation (2026-02-26):** `ADMIN_UI_DESIGNER` permission-role eşlemesi (super_admin/country_admin), `ui_configs/ui_themes/ui_theme_assignments` modelleri + `p59_ui_designer_foundation` migration, `/api/admin/ui/configs/*`, `/api/ui/*`, theme assignment + effective resolve endpointleri, `/admin/user-interface-design` 3 sekmeli admin iskeleti (gerçek GET/POST roundtrip), test raporu: `/app/test_reports/iteration_25.json` (PASS).
- **P60 UI Designer Sprint 2 Slice (2026-02-26):** Kurumsal header 3 satır drag&drop editör + Row1 logo upload (png/svg/webp, 2MB, 3:1 ±%10), `ui_logo_assets` lifecycle tablosu + `p60_ui_logo_assets` migration, logo soft-replace (`is_replaced`) + 7 gün retention cleanup endpointi (`/api/admin/ui/logo-assets/cleanup`), token bazlı tema form editörü + backend token validation, config-driven header render entegrasyonu (Dealer/User/Public fallback), dashboard widget order fallback mantığı. Test raporu: `/app/test_reports/iteration_26.json` (PASS, 1 low test skipped; manual >2MB upload testi ayrıca doğrulandı).
- **Tema Yönetimi (2026-02-25):** Semantik CSS değişkenleri, light/dark palette standardizasyonu, FOUC önleyici theme-init script, root ErrorBoundary + wizard/detail boundary.
- **Footer Domain (2026-02-25):** Footer grid builder (row/1-5 column + LinkGroup/Metin/Sosyal), draft/publish + preview, versioning + rollback, admin Footer Yönetimi ve Bilgi Sayfaları CRUD.
- **Header Domain (2026-02-25):** MainLayout ile public header merkezi; site_header_config modeli + logo upload + cache invalidation (versiyonlu logo_url); admin Header Yönetimi ekranı; guest/auth header state ve responsive menü; logo yoksa asset request atılmaz.
- **Pricing Campaign Time Range (2026-02-25):** start_at/end_at zorunlu, overlap kontrolü (409), planlı/aktif/süresi doldu statüsü, quote sadece zaman aralığında.
- **Pricing Campaign CRUD (2026-02-25):** pricing_campaign_items modeli + migration; admin bireysel/kurumsal kampanya CRUD; quote engine kampanya item’larına geçirildi; checkout snapshot kampanya item referansıyla kilitlendi; expiry job campaign item end_at sonrası pasif.
- **Pricing Part 2 (2026-02-25):** pricing_campaign policy modeli + override hook + expire job + audit; Admin Kampanya Modu gerçek yönetim ekranı.
- **Pricing Part 1 Scaffold (2026-02-25):** domains/ads_engine + domains/pricing_engine, /api/admin/pricing/campaign + /api/pricing/quote + /api/pricing/packages iskeletleri, Admin “Fiyatlandırma” menüsü ve placeholder sayfalar, pricing_manager role + RBAC.
- **Campaign Uyarı MVP (2026-02-25):** end_at 3 gün uyarısı + trafik artışı %200 uyarısı + budget info (aktif kampanya); eşikler .env (END_WARNING_DAYS/TRAFFIC_SPIKE_THRESHOLD).
- **Campaign CRUD (2026-02-25):** /admin/ads/campaigns ekranı, kampanya create/edit/pause, bağlı reklamlar tabı + link/unlink; ads_manager rolü ve RBAC yetkileri.
- **Tek Aktif Reklam Kuralı (2026-02-25):** placement başına tek aktif reklam, format matrisi (horizontal/vertical/square), UI çakışma uyarısı + DB partial unique index (uq_ads_active_placement).
- **P47 Ads Format + Unique Migration (2026-02-25):** ads.format kolonu + aktif reklam dedup + unique index.
- **Campaign Analytics (2026-02-25):** ad_campaigns tablosu + ads.campaign_id; analytics group_by=ad|campaign|placement; KPI aktif reklam sayısı; kampanya süresi bitince bağlı reklamlar pasife düşer.
- **Ad Analytics (2026-02-24):** ad_impressions/ad_clicks tabloları, impression dedup (30dk), /api/ads/{id}/impression ve /api/ads/{id}/click, /api/admin/ads/analytics, Admin Ads Performans sekmesi, public AdSlot (Home/Search/Login).
- **P46 Ad Campaigns Migration (2026-02-25):** ad_campaigns + ads.campaign_id idempotent migration + alembic upgrade heads.
- **P45 Ad Analytics Migration (2026-02-24):** idempotent migration + alembic upgrade heads.
- **P0 Kanıt Paketi (2026-02-24):** /app/docs/P0_EVIDENCE.md (login + migration + health + frontend PASS)
- **P1 Route Map + API Contract (2026-02-24):** /app/architecture/ui/P1_PUBLIC_SITE_CONSOLE_V1.md
- **Admin Login UX (2026-02-24):** giriş sonrası “Oturum doğrulandı” → “Admin paneli yükleniyor...” toast akışı
- **Placement Enum Standardizasyonu (2026-02-24):** AD_HOME_TOP, AD_CATEGORY_TOP, AD_CATEGORY_RIGHT, AD_CATEGORY_BOTTOM, AD_SEARCH_TOP, AD_IN_FEED, AD_LISTING_RIGHT, AD_LOGIN_1, AD_LOGIN_2
- **Doping State Machine (2026-02-24):** requested → paid → approved → published → expired (paid zorunlu)
- **Router Binding Fix (2026-02-24):** api_router + RBAC allowlist tüm route’ları kapsayacak şekilde dosya sonuna taşındı
- **P44 Site Content Migration (2026-02-24):** migration_dry_run PASS; p44 migration idempotent guard; alembic upgrade heads ile şema başa taşındı.
- EU panel dokümantasyon paketi (/app/docs/CONSUMER_IA_V1.md, DEALER_IA_V1.md, PRIVACY_CENTER_EU.md, DATA_MODEL_SPEC_EU_PROFILES_V1.md)
- ConsumerProfile ve DealerProfile modelleri
- DealerProfile için gdpr_deleted_at alanı (model + migration: p34_dealer_gdpr_deleted_at)
- Helper: lazy create + VAT regex doğrulama + profile response builder
- **Yeni v1 endpointler:**
  - GET/PUT /api/v1/users/me/profile (consumer)
  - GET/PUT /api/v1/users/me/dealer-profile (dealer)
  - GET/PUT /api/v1/dealers/me/profile (alias)
  - GET/POST /api/v1/users/me/2fa/* (status/setup/verify/disable)
  - GET /api/v1/users/me/data-export (JSON)
  - DELETE /api/v1/users/me/account (soft delete + 30 gün + is_active=false)
- Frontend (Consumer Panel): AccountProfile + PrivacyCenter yeni v1 endpointlerine bağlı
- **Portal yeniden tasarımı (EU uyumlu):**
  - Turuncu zemin + üst yatay menü + sol alt menü
  - Bireysel/Ticari menü farkları uygulandı
  - TR/DE/FR menü dili toggle
- Dealer portal ek sayfalar: Şirket Profili + Gizlilik Merkezi
- **Admin kategori modalı:**
  - Hiyerarşi adı → Kategori
  - Seviye bazlı sütunlar: her seviyede çoklu kategori kartı + Tamam ile bir sonraki seviyeye geçiş
  - Alt seviye kolonları, seçilen kategoriye göre açılıyor
  - Seviye Tamam: ad/slug doluysa tüm kartları tamamlar ve sonraki seviyeyi açar
  - Düzenle: kilitlenen seviye/öğe yeniden açılabilir
  - Akış: her adımda "Devam" (Next), son adımda "Kaydet"
- **Admin kategori parametre alanları:**
  - Parametre alanlarında seçenekleri tek tek ekleme/çıkarma arayüzü
  - Parametre listesinde seçenek ve zorunluluk özetleri
- **Admin kategori sihirbazı P0 düzeltmeleri (2026-02-22):**
  - Tamam → PATCH (server response authoritative)
  - Next gating + tooltip: “Önce bu adımı tamamlayın.”
  - Kategori → Çekirdek Alanlar → Parametre Alanları sırası enforce
- **Admin kategori sihirbazı Edit Mode state sync (2026-02-23):**
  - wizard_progress backend tek kaynak; save/unlock sonrası UI store güncelleniyor
  - Edit unlock başarısızsa snapshot rollback
  - Downstream dirty adımlar UI’da görünür
- **Admin Dirty CTA + Analytics (2026-02-23):**
  - “Sıradaki eksik adımı tamamla” CTA + ilk dirty tab yönlendirmesi
  - admin_dirty_cta_clicked / admin_dirty_first_step_opened payload (category_id, step_id, admin_user_id, wizard_state)
- **Son Seçiminiz (2026-02-23):**
  - user_recent_categories tablosu + upsert + GET endpoint
  - Drill-down ekranında kategori adı + breadcrumb + modül + ülke kartı
  - Vehicle modülünde /account/create/vehicle-wizard yönlendirmesi
- **İlan Ver (Emlak) yeni akış:**
  - /ilan-ver/kategori-secimi sütunlu drill-down + breadcrumb + arama kutusu
  - /ilan-ver/detaylar placeholder (detay formu daha sonra)
  - /api/categories/children + /api/categories/search endpointleri

- **İlan ver sihirbazı (create listing):**
  - Başlıklar/boş durumlar/section alanları için data-testid eklendi
  - Dropzone + cover etiketleri test-id ile tamamlandı
- **Çekirdek Alanlar fiyat tipi (2026-02-23):**
  - price_type (FIXED/HOURLY) + hourly_rate desteği (backend + frontend)
  - Fiyat/Saatlik Ücret toggle + tek input swap + doğrulama mesajları
  - Public detay ve aramada “{amount} {currency}” / “{rate} {currency} / saat”
  - Fiyat filtresi yalnız FIXED ilanlara uygulanıyor
- **Listing wizard altyapı stabilizasyonu (2026-02-23):**
  - /api/catalog/schema draft schema erişimi açıldı (wizard blokları kalktı)
  - /api/v2/vehicle/makes + models SQL fallback eklendi
- **Premium otomobil ilan sihirbazı P0 (2026-02-23):**
  - Model grid + arama + seçim (geri/ileri persist)
  - Yıl dropdown (2010–2026) + opsiyonel Versiyon/Donanım metin alanı
  - Make/Model/Year Next autosave + “Kaydedildi” toast + step değişiminde scroll-to-top (preview hariç)
  - Autosave analytics eventleri: wizard_step_autosave_success / wizard_step_autosave_error
  - Yıl adımı model seçilmeden kilitli + state sync
  - Oto çekirdek alanları: km, yakıt, vites, çekiş, kasa, motor cc/hp, hasar, takas, konum + fiyat tipi entegrasyonu
  - Özellikler/Medya: min 3 foto + kapak + sıralama, review’da galeri özeti
  - Önizleme: marka/model/yıl, fiyat tipi, motor, konum, özellik özetleri
  - Draft save PATCH + create draft make/model opsiyonel
  - Şema yükleme 409 notice + kullanıcıya bilgi mesajı
  - DB client_encoding UTF8 (TR karakterler)
  - App.js VehicleSegmentPage import fix
- **Kategori import/export (2026-02-23):**
  - CSV + XLSX export (module + country filtreleri)
  - Import dry-run + apply, slug ile eşleştirme, wizard_progress taşıma
  - Validasyon: zorunlu alanlar, duplicate slug, cycle, satır hata raporu
  - Audit log (import.dry_run, import.apply)
  - Örnek dosyalar: backend/tests/fixtures/categories-import-sample.(csv/xlsx)
- **Kategori import/export P0.1 (2026-02-23):**
  - Örnek CSV/XLSX indir endpoint’leri (module/country filtreli)
  - schema_version = v1 kolonlu şablon + root/child örnek satır
- **Genel “İlan Ver” drill-down (P1 başlangıcı, 2026-02-23):**
  - Modül seçimi + L1..Ln kategori drill-down + arama
  - Son Seçiminiz kartı (breadcrumb + module + ülke)
  - Vehicle modülü → /account/create/vehicle-wizard, diğerleri → /account/create/listing-wizard
  - Analytics event’leri: step_select_module, step_select_category_Ln
  - /api/analytics/events endpointi audit log ile kayıt
- Preview/Prod DB fail-fast: CONFIG_MISSING hatası + localhost yasak + DB_SSL_MODE=require
- .env override kapatıldı (server.py, core/config.py, app/database.py)
- **P0 Sertleştirmeler:**
  - /api/health/db → migration_state gate + 60sn cache + last_migration_check_at
  - /api/health → config_state + last_migration_check_at + ops_attention + last_db_error
  - Register honeypot (company_website) + server-side reject + audit log (register_honeypot_hit)
  - GDPR export completion notification (in-app, warning) + audit trail
- **Mongo temizliği (moderasyon):**
  - Moderation queue/count/detail SQL’e taşındı
  - Approve/Reject/Needs‑revision SQL akışı + ModerationAction + audit log
  - Geçici ETL endpointi kaldırıldı (Mongo runtime cleanup başlangıcı)
- **Moderation Freeze UI (2026-02-24):**
  - Admin System Settings toggle kartı metinleri + açıklama notu güncellendi
  - Moderation Queue + detay + aksiyon diyaloglarında banner gösterimi
  - Approve/Reject/Needs Revision aksiyonları disable + tooltip
- **Local Infra:**
  - PostgreSQL kuruldu, app_local DB oluşturuldu
  - Alembic upgrade heads PASS
  - Stripe CLI kuruldu (auth/test key invalid → idempotency BLOCKED)
- **Preview E2E:**
  - Admin login + Moderation Queue PASS
  - Consumer/Dealer login + profil endpointleri PASS
- **DB 520 Stabilizasyonu (2026-02-23):**
  - SQLAlchemy pool konfigürasyonu için runtime “effective config” logu + pool lifecycle logları (INFO + debug flag)
  - get_db / get_sql_session: rollback + deterministic close
  - CorrelationIdMiddleware aktif + DB error loglarında request_id
  - Load test: Faz‑1 1000 sequential login+me, Faz‑2 10 paralel toplam 1000 istek → 0 adet 520 (p95 ~2924ms / 5074ms)
  - /app/load_test.py eklendi
  - P1 smoke: Auth + Vehicle wizard + Admin categories edit modal PASS
- **Wizard Autosave Status Badge (2026-02-23):**
  - Badge metni: “Kaydedildi • HH:MM” (backend updated_at)
  - Hata: “Kaydedilemedi”
- **System Health Mini-Badge (2026-02-23):**
  - /api/admin/system/health-summary endpointi + 60sn cache
  - Admin header badge (DB status, last check, 5dk error rate)
- **System Health Detail Panel (2026-02-23):**
  - /api/admin/system/health-detail endpointi + 60sn cache
  - 24s hata oranı sparkline + DB latency avg/p95 + son ETL zamanı
  - Slow queries (24s) rozeti, threshold >800ms
  - Endpoint bazlı slow query kırılımı (/api/search, /api/listings, /api/admin/*)
- **CDN Metrics Adapter (Cloudflare) (2026-02-23):**
  - Health panel CDN hit ratio, origin fetch, warm/cold p95 (feature-flag)
  - Country breakdown + sparkline + canary status + cf_ids_present/source
- **Cloudflare Config Admin UI (2026-02-23):**
  - System Settings kartı + masked inputs + canary test
  - CONFIG_ENCRYPTION_KEY health flag + save guard + failure reason logs
  - Tek durum mesajı + kullanıcı dostu canary + teknik detay tooltip
- **Phase A Ops Inject Closeout (2026-02-23):** env/secret inject + canary OK + kanıt: `/app/docs/ADMIN_V1_PHASE_A_EVIDENCE.md`
- **Phase B RBAC Hard Lock Kickoff (2026-02-23):** deny-by-default allowlist + admin UI guard + docs: `/app/docs/RBAC_MATRIX.md`, `/app/docs/RBAC_ENDPOINT_MAP.md`, `/app/docs/RBAC_NEGATIVE_TESTS.md`
- **Data Layer Cutover Kickoff (Mongo Tasfiye) (2026-02-23):**
  - Mongo envanteri + dönüşüm haritası + şema gap raporu
  - P0 admin chain SQL: system-settings + admin invite (520 → 0)
  - Dokümanlar: `/app/docs/MONGO_INVENTORY.md`, `/app/docs/MONGO_TO_SQL_MAP.md`, `/app/docs/SQL_SCHEMA_GAP_REPORT.md`, `/app/docs/SQL_SCHEMA_COMPLETION_PACKAGE.md`, `/app/docs/MONGO_SQL_MIGRATION_PLAN.md`, `/app/docs/MONGO_SQL_MIGRATION_EVIDENCE.md`
- **Dependency Resolver Fix (2026-02-23):**
  - google-api-core hard pin kaldırıldı, dar aralıkla sabitlendi (>=2.28.1,<2.31.0)
- **Admin Kategori Manuel Yönetimi (2026-02-23):**
  - Modül seçimi + parent validation + alt tip metadata
- **İlan Ver Kategori Fallback (2026-02-23):**
  - Veri yoksa güvenli fallback + CTA
- **Search Postgres Cutover (2026-02-23):**
  - SEARCH_SQL_ROLLOUT %50 → %100
  - Seed demo data (5000 ilan) + ETL tekrar çalıştırıldı
  - Parity + benchmark raporları güncellendi
  - Pending Ops 24h monitoring: /app/memory/SEARCH_24H_MONITORING_REPORT.md
  - Raporlar: /app/memory/SEARCH_PARITY_REPORT.md, /app/memory/SEARCH_PARITY_RAW.md, /app/memory/SEARCH_BENCHMARK_REPORT.md, /app/memory/SEARCH_SLOW_QUERIES.md
- **Moderation Items Migration (2026-02-23):**
  - moderation_items SQL tablosu + model + Pydantic schema
  - p38 migration uygulandı
  - ETL: scripts/migrate_moderation_items_from_mongo.py (reason sanitize + status normalize + UTC)
  - Parity raporu: /app/memory/MODERATION_PARITY_REPORT.md (sample 50)
  - ETL (admin ops) çalıştırıldı; Mongo moderation_queue bulunamadı (count=0)
  - Admin moderation queue/count SQL artık moderation_items üzerinden
  - Listing submit/request-publish sırasında moderation_item upsert
  - Cutover plan: /app/memory/MODERATION_CUTOVER_PLAN.md

## Kanıtlar
- /app/docs/LOCAL_DB_READY_EVIDENCE.md
- /app/docs/MIGRATION_DRIFT_SIMULATION_EVIDENCE.md
- /app/docs/STRIPE_CLI_INSTALL_EVIDENCE.md
- /app/docs/STRIPE_IDEMPOTENCY_LOCAL_EVIDENCE.md
- /app/docs/STRIPE_IDEMPOTENCY_EVIDENCE.md
- /app/docs/P0_1_SECURITY_HARDENING_CLOSED.md
- /app/docs/LOGIN_RATE_LIMIT_EVIDENCE.md
- /app/docs/TWO_FACTOR_CHALLENGE_EVIDENCE.md
- /app/docs/TWOFA_BACKUP_CODE_EVIDENCE.md
- /app/docs/PUBLIC_SEARCH_MONITORING_REPORT.md
- /app/docs/RBAC_COVERAGE_GATE.md
- /app/docs/RBAC_CI_PR_COMMENT_DECISION.md
- /app/docs/MODERATION_FREEZE_WINDOW_PLAN.md
- /app/docs/ADMIN_INVITE_PREVIEW_SPEC.md
- /app/docs/GDPR_EXPORT_NOTIFICATION_EVIDENCE.md
- /app/docs/GDPR_EXPORT_SOFT_DELETE_E2E.md
- /app/docs/AUTH_SECURITY_STRESS_EVIDENCE.md
- /app/docs/AUDIT_CHAIN_PARITY_EVIDENCE.md
- /app/docs/HEALTH_OPS_VISIBILITY_SPEC.md
- /app/docs/PROFILE_ENDPOINT_FIX_EVIDENCE.md
- /app/docs/PREVIEW_DB_FIX_EVIDENCE.md
- /app/docs/PREVIEW_MIGRATION_EVIDENCE.md
- /app/docs/HEALTH_MIGRATION_GATE_SPEC.md
- /app/docs/HEALTH_MIGRATION_GATE_EVIDENCE.md
- /app/docs/HEALTH_MIGRATION_GATE_PREVIEW_EVIDENCE.md
- /app/docs/PREVIEW_MIGRATION_PARITY_EVIDENCE.md
- /app/docs/SPRINT1_PREVIEW_API_EVIDENCE.md
- /app/docs/SPRINT1_PREVIEW_E2E_EVIDENCE.md
- /app/docs/SPRINT_PREVIEW_ADMIN_E2E_EVIDENCE.md
- /app/docs/SPRINT1_CLOSEOUT.md
- /app/docs/ADMIN_V1_PHASE_A_EVIDENCE.md
- /app/docs/MONGO_INVENTORY.md
- /app/docs/MONGO_TO_SQL_MAP.md
- /app/docs/SQL_SCHEMA_GAP_REPORT.md
- /app/docs/SQL_SCHEMA_COMPLETION_PACKAGE.md
- /app/docs/MONGO_SQL_MIGRATION_PLAN.md
- /app/docs/MONGO_SQL_MIGRATION_EVIDENCE.md
- /app/docs/FINAL_520_ZERO_REPORT.md
- /app/docs/DATA_LAYER_CUTOVER_CLOSED.md
- /app/memory/MONGO_INVENTORY.md
- /app/docs/RBAC_MATRIX.md
- /app/docs/RBAC_ENDPOINT_MAP.md
- /app/docs/RBAC_NEGATIVE_TESTS.md
- /app/docs/REGISTER_ANTIBOT_HONEYPOT_SPEC.md
- /app/docs/REGISTER_ANTIBOT_HONEYPOT_EVIDENCE.md
- /app/docs/GDPR_EXPORT_NOTIFICATION_SPEC.md
- /app/docs/GDPR_EXPORT_NOTIFICATION_EVIDENCE.md
- /app/docs/GDPR_EXPORT_SOFT_DELETE_E2E.md
- /app/docs/OPS_ESCALATION_TICKET.md
- /app/docs/PREVIEW_UNBLOCK_TRACKER.md
- /app/docs/LOCAL_PREVIEW_SIMULATION_EVIDENCE.md
- /app/docs/PREVIEW_ACTIVATION_RUNBOOK.md
- /app/memory/MONGO_TO_POSTGRES_MIGRATION_PLAN.md
- /app/memory/SEARCH_PARITY_REPORT.md
- /app/memory/SEARCH_PARITY_RAW.md
- /app/memory/SEARCH_BENCHMARK_REPORT.md
- /app/memory/SEARCH_SLOW_QUERIES.md
- /app/memory/SEARCH_EXPLAIN_ANALYZE_RAW.md
- /app/memory/SEARCH_CUTOVER_PLAN.md
- /app/memory/SEARCH_24H_MONITORING_REPORT.md
- /app/memory/MODERATION_PARITY_REPORT.md
- /app/memory/MODERATION_CUTOVER_PLAN.md
- /app/memory/MONGO_DEPENDENCY_REPORT.md
- /app/memory/ADR.md
- /app/memory/LISTING_ENTRY_FLOW_ACCEPTANCE_CRITERIA.md
- /app/memory/ROADMAP.md
- /app/memory/CDN_24H_REPORT.md
- /app/memory/UX_THEME_PHASE_PREP.md
- /app/docs/P1_PRICING_CAMPAIGN_CRUD_EVIDENCE.md
- /app/docs/PRICING_TEST_USER_SEED.md
- /app/docs/P1_RBAC_VALIDATION_EVIDENCE.md
- /app/docs/P1_HEADER_EVIDENCE.md
- /app/docs/P1_FOOTER_EVIDENCE.md
- /app/docs/UI_STYLE_GUIDE.md
- /app/docs/P1_THEME_EVIDENCE.md
- /app/docs/P1_CROSS_BROWSER_EVIDENCE.md
- /app/docs/P1_PERFORMANCE_REPORT.md
- /app/docs/P1_SECURITY_UI_CHECKLIST.md

## Son Değişiklikler (2026-02-25)
- Public UI hardening: SEO meta + OG + schema; CSP header; 404/500 sayfaları; cross-browser/perf/security dokümanları.
- Tema yönetimi: CSS değişkenleri + FOUC script + ErrorBoundary; hex renkler semantik değişkenlere taşındı.
- Footer domain: grid builder + draft/publish + preview + version rollback; Bilgi Sayfaları CRUD + /bilgi/:slug.
- Header domain: MainLayout + site_header_config modeli + logo upload/cache invalidation; Admin Header Yönetimi ekranı + guest/auth header state.
- Pricing Campaign Items modeli + migration (pricing_campaign_items) ve snapshot alanları (campaign_item_id, listing_quota, publish_days, campaign_override_active).
- Quote engine kampanya item’larına geçirildi; checkout snapshot kampanya item referansı ile kilitleniyor.
- Admin UI: Bireysel/Kurumsal Kampanyalar CRUD + modal.
- Start/end datetime zorunluluğu + overlap kontrolü (scope bazlı) + status kolonları; quote sadece aktif aralıkta.
- RBAC: pricing_manager ve ads_manager erişim ayrımı + menü filtreleme + endpoint 403 doğrulaması (P1_RBAC_VALIDATION_EVIDENCE.md).
- Expiry job: campaign item end_at sonrası otomatik pasif.
- Test kullanıcı seed script + ops doküman + P1_PRICING_CAMPAIGN_CRUD_EVIDENCE.md.

## Son Değişiklikler (2026-02-24)
- P0.1 kapanış paketleri hazırlandı: P0_1_SECURITY_HARDENING_CLOSED.md + backup code + log-based 24h raporu.
- 2FA backup code tek-kullanım kanıtlandı (curl + UI).
- Public search log-based 24h window CLOSED olarak raporlandı.
- Moderation freeze window planı kilitlendi.
- RBAC CI PR comment workflow güncellendi + karar dokümante edildi.
- Moderation Freeze UI: Admin System Settings toggle metni güncellendi + Moderation Queue banner/tooltip/disable davranışı tamamlandı.
- Moderation Freeze reason alanı + audit event (ENABLED/DISABLED) + banner reason gösterimi eklendi.
- Moderation Freeze evidence + closeout: MODERATION_FREEZE_EVIDENCE.md, MODERATION_FREEZE_CLOSED.md.
- Privacy Center Export History (gdpr_exports tablosu + 30 gün retention + /account/privacy Export Geçmişi tabı) tamamlandı.
- FAZ-UH1 dokümantasyonu tamamlandı: /architecture/ui/* (purpose, data sources, IA v2, wireframe, backlog, tokens).
- Consumer Dashboard V1 aksiyon odaklı yeniden kuruldu (KPI row, primary CTA, listing snapshot, favoriler/saved search, status banner).
- /account/security route eklendi + sol menü IA V2 güncellendi.
- UH1 closeout + regression checklist + Quick Preview spec + P2 dependency dokümanları yayınlandı.
- FAZ-ADMIN-FINAL Sprint1 dependency map + gap list + implementation order + ticket taslağı oluşturuldu.
- AF Sprint1 migration impact analizi tamamlandı (/architecture/admin/AF_SPRINT1_MIGRATION_IMPACT.md).
- Migration dry-run katmanı eklendi (scripts/migration_dry_run.py + spec + runbook gate + PR checkbox + CI job).
- AF-G1/2/3 uygulandı: risk_level + ban_reason + suspension guard, plan quota max + discount constraint, bulk moderation transactional precheck.
- Admin UI: Dealer risk level kontrolü + Plan quota max doğrulaması.
- Dry-run audit log opsiyonu eklendi (MIGRATION_DRY_RUN).

## Son Güncellemeler (2026-02-25)
- Tema Yönetimi admin ekranı: Light/Dark edit, live preview, draft/publish, versiyon listesi + rollback.
- SiteThemeConfig modeli + admin/public API + WCAG AA kontrast validasyonu + cache refresh döngüsü.
- Header authenticated CTA “İlan Ver” mobil görünür; header/footer renkleri admin değişkenleriyle yönetiliyor.
- Admin sidebar “Kampanyalar” menüsü kaldırıldı; route + RBAC temizliği yapıldı.
- Reklam soft delete: endpoint + UI confirm modal + AD_DELETED audit.
- Tema altyapısı: CSS hex hard-code temizliği, ThemeContext + index.html pre-load config.
- Araç Master Data Import modülü: job tabanlı API/JSON upload, dry-run, upsert make/model/trim, log/summary, RBAC masterdata_manager, 50MB limit.
- JSON validation iyileştirmeleri: parse/schema/business ayrımı + field_errors + örnek JSON indirme + schema dokümantasyonu.
- Vehicle Selector Engine: /api/vehicle/* endpointleri + /ilan-ver araç seç adımı (trim zorunluluk kuralı).
- Kategori sıra revizyonu: otomatik sıra, parent scope unique index, reindex migrasyonu, admin UI read-only.
- Kanıt: /app/docs/P1_VEHICLE_MASTERDATA_IMPORT_EVIDENCE.md
- Kanıt: /app/docs/P1_VEHICLE_SELECTOR_EVIDENCE.md
- Kanıt: /app/docs/P1_CATEGORY_ORDER_EVIDENCE.md

## Mimari Kararlar (ADS)
- **ADS-57 — Pricing Campaign Item CRUD:** Sabit paket/tier yerine pricing_campaign_items ile bireysel/kurumsal kampanya item’ları yönetilir.
- **ADS-58 — Deprecate:** pricing_packages ve pricing_tier_rules UI’dan kaldırıldı, DB’de deprecated olarak tutulur.
- **ADS-59 — (Deprecated) Tek aktif kural:** ADS-65 ile değiştirildi (zaman aralığı kesişmesi yok).
- **ADS-60 — Soft delete:** Kampanya item silme soft-delete (is_deleted/deleted_at).
- **ADS-64 — Kampanya zamanı:** start_at/end_at zorunlu (datetime) + UTC normalize.
- **ADS-65 — Overlap kuralı:** Aynı scope’ta zaman aralığı kesişen aktif kampanya oluşturulamaz.
- **ADS-67 — RBAC P1 kapanış:** pricing/ads domainleri kesin ayrılır, endpoint decorator zorunlu.
- **ADS-68 — Kampanya Timeline UI P2:** Gantt/timeline görünümü P2 backlog.
- **ADS-69 — Header Global Layout:** Public header tek MainLayout üzerinden çalışır.
- **ADS-70 — Tek aktif header config:** site_header_config üzerinde is_active unique.
- **ADS-71 — Auth state layout-level:** Header auth kontrolü layout seviyesinde yapılır.
- **ADS-74 — Header chip önerileri:** arama chip’leri P2 backlog.
- **ADS-75 — Logo fallback 404:** logo yoksa asset request atılmaz, sadece fallback text.
- **ADS-76 — Footer ana faz:** Footer (grid builder + bilgi sayfaları) bir sonraki ana teslim.
- **ADS-81 — Public Layout Freeze:** Header+Footer+Theme feature-freeze.
- **ADS-82 — Tema toggle public header’a eklenmez.
- **ADS-83 — Public UI Production sertifikasyon:** Lighthouse + Cross-browser + Security checklist tamamlanmadan kapatılmaz.
- **ADS-98 — Import job:** Araç Master Data Import işlemi job olarak yürütülür.
- **ADS-99 — Upsert + no-delete:** Import sadece insert/update yapar, silme yok.
- **ADS-100 — Unique key:** trim_id varsa onu, yoksa year+make+model+trim anahtarı kullanılır.
- **ADS-101 — Provider config env:** VEHICLE_TRIMS_API_* değerleri sadece env/secret ile gelir.
- **ADS-102 — Upload limit 50MB:** JSON upload max 50MB + parse guard.
- **ADS-103 — Dry-run raporu:** new/updated/skipped + distinct counts + validation errors + estimated süre.
- **ADS-104 — RBAC rolü:** masterdata_manager rolü sadece import ekranı ve job endpointlerine erişir.
- **ADS-105 — Job altyapısı:** DB job tablosu + BackgroundTasks (MVP), 30dk timeout.
- **ADS-VEH-01 — Vehicle Selector ayrı domain:** Vasıta detay seçimi kategori değil selector engine ile yapılır.
- **ADS-IMP-01 — JSON validasyon 3 katman:** parse → schema → business ayrımı.
- **ADS-CAT-01 — Kategori sıra otomatik:** parent scope unique + reindex.

## Blokajlar / Riskler
- Cloudflare config kaydı için CONFIG_ENCRYPTION_KEY gerekli (preview env sağlandı; eksikse kaydetme bloklanır)

## Öncelikli Backlog
### P0 (Hemen)
- ✅ Data Layer Cutover (Mongo Tasfiye): Mongo 0-iz + 520=0 + Dealer/Consumer E2E tamamlandı
- ✅ Admin V1 Phase B (RBAC Final Freeze): MATRIX/ENDPOINT MAP FREEZE v1 + negatif test kanıtları + portal guard doğrulaması
- ✅ Preview GDPR export + soft delete E2E kanıtları + audit doğrulaması
- ✅ Honeypot 400 + register_honeypot_hit audit doğrulaması (preview)
- ✅ Stripe idempotency testi (Checkout flow)

### P0.1 (Güvenlik Doğrulama)
- ✅ Login rate limit tetikleme testi (preview)
- ✅ 2FA challenge (enable → wrong OTP → success) kanıtı (preview)
- ✅ 2FA backup code tek kullanımlık testi (preview)
- ✅ Soft delete → login blocked testi (preview)
- ✅ GDPR export sonrası notification banner UI doğrulaması

### P1 (Aktif)
- ✅ Public Search 24h monitoring: log-based 24h CLOSED
- ✅ Moderation migration: SQL parity report + freeze window plan kilitlendi
- 🔵 Admin Operasyonel Finalizasyon (FAZ-ADMIN-FINAL) başlatıldı
- ✅ Pricing RBAC doğrulama (pricing_manager / ads_manager)

### P1 (Sprint‑1 closeout)
- Sprint‑1 E2E kanıt paketi

### P1.5 / P2 (Enhancement)
- ✅ Privacy Center export geçmişi (gdpr_exports tablosu + UI) → /app/docs/PRIVACY_EXPORT_HISTORY_SPEC.md
- 🔵 Quick Preview Modal (UH1-E1) — /architecture/ui/LISTING_QUICK_PREVIEW_SPEC.md

### P2
- Header arama chip önerileri (P2)
- Kampanya timeline/gantt görünümü + overlap uyarısı (pricing)
- Pricing Konfigürasyon ekranı (eşik/parametre yönetimi)
- Kayıtlı Arama/Alert (P2 backlog, P1 kapsamına girmez)
- P2 Saved Search Integration → /architecture/ui/P2_SAVED_SEARCH_INTEGRATION.md
- P2 Quota API Binding → /architecture/ui/P2_QUOTA_API_BINDING.md
- VIES VAT doğrulama (API)
- GDPR CSV export
- Public search + admin listings Mongo bağımlılıklarının SQL’e taşınması
- Verification token cleanup job

---

## 2026-02-25 — P0 Vehicle Selector Stabilizasyon Güncellemesi

### Tamamlananlar (P0)
- `ListingWizard` araç akışında zincir seçim stabilizasyonu tamamlandı:
  - Year değişiminde Make/Model/Trim ve bağlı filtre state’leri temizleniyor.
  - Make değişiminde Model/Trim ve bağlı filtre state’leri temizleniyor.
  - Model/filtre değişiminde trim listesi yeniden yükleniyor (race-condition guard ile).
- `year >= 2000` için trim zorunluluğu hem UI hem backend tarafında enforce edildi.
- `year < 2000` için manuel trim override akışı eklendi ve backend doğrulaması aktif edildi.
- Wizard merkezi state’e aşağıdaki alanlar eklendi ve persist edildi:
  - `vehicle_trim_id`, `vehicle_trim_label`, `manual_trim_flag`, `manual_trim_text`
  - `trim_filter_fuel`, `trim_filter_body`, `trim_filter_transmission`, `trim_filter_drive`, `trim_filter_engine_type`
- Category değişiminde vehicle state reset kuralı eklendi (ghost-state engeli).
- Kanıt dokümanı oluşturuldu: `/app/docs/P0_VEHICLE_SELECTOR_FIX_EVIDENCE.md`

### Teknik Dosyalar
- Frontend:
  - `frontend/src/pages/user/wizard/Step2Brand.js`
  - `frontend/src/pages/user/wizard/Step3Model.js`
  - `frontend/src/pages/user/wizard/Step4YearTrim.js`
  - `frontend/src/pages/user/wizard/Step4Review.js`
  - `frontend/src/pages/user/wizard/WizardContext.js`
- Backend:
  - `backend/server.py`

### Test Durumu
- Testing agent raporu: `/app/test_reports/iteration_12.json` (core P0 senaryolar PASS)
- Ek self-test (curl):
  - `/api/vehicle/years|makes|models|options|trims` → 200
  - `year>=2000` + trimsiz payload → 422
  - `year<2000` + manualsız payload → 422
  - geçerli modern/manual payload → 200

### Kalan Backlog
- **P1 (beklemede):** country_code genişletmesi, import job CSV/retry, admin module type iyileştirmesi
- **P2:** kampanya timeline, doping sistemi, public campaign UI

---

## 2026-02-26 — P0 Resmi Kapanış + P1 Meilisearch Config History (Başlangıç)

### Sprint Kararı
- P0 statüsü resmi olarak **CLOSED**.
- P1 aktif faza alındı (ilk teslim: Search Config yönetim katmanı).

### Bu tur tamamlananlar (P1.1 temel katman)
- Admin System Settings içine yeni kart eklendi: **Search / Meilisearch**
  - `Aktif Konfig` sekmesi
  - `Geçmiş` sekmesi
- Backend’de versioned config şeması eklendi:
  - `meilisearch_configs`
  - `status`: `active | inactive | revoked`
  - `meili_master_key_ciphertext` şifreli saklama
  - `last_tested_at`, `last_test_result (PASS/FAIL + reason_code)`
- Aktivasyon kapısı eklendi:
  - Kaydet = yalnızca `inactive`
  - Aktivasyon = zorunlu test + PASS
  - FAIL durumda konfig aktifleşmez
- Geçmişten rollback/reuse akışı eklendi:
  - Geçmiş satırından tek tık “Bu konfigi tekrar aktif et”
  - Aktivasyon öncesi otomatik test çalışır
- RBAC uygulandı:
  - Sadece `super_admin` bu kartı ve endpointleri görebilir/değiştirebilir
- Audit log event’leri eklendi:
  - `MEILI_CONFIG_CREATE`
  - `MEILI_CONFIG_TEST`
  - `MEILI_CONFIG_ACTIVATE` / `MEILI_CONFIG_ACTIVATE_REJECTED`
  - `MEILI_CONFIG_REVOKE`

### Güvenlik Kuralları
- Master key hiçbir API cevabında plaintext dönmez.
- History listesinde yalnızca `master_key_masked` gösterilir.
- UI key alanı her zaman boş/maskeli başlar.

### Doğrulama ve Kanıt
- Kanıt dosyası: `/app/docs/P1_MEILI_CONFIG_HISTORY_EVIDENCE.md`
- İçerilen testler:
  - PASS config aktivasyon (mock meili)
  - FAIL config aktivasyon (connection_error)
  - FAIL sonrası önceki aktif konfigin korunması (rollback davranışı)
  - RBAC 403 doğrulaması

### Bu tur dokunulmadı
- P1.2 listing→index senkron hooklarının tam kapsamı (partial değil, bir sonraki adımda devam)
- Facet/autocomplete/search UI (P1.3+)

---

## 2026-02-26 — P1.2 Listing → Index Senkronizasyonu (Core) Tamamlandı

### Teslim Edilenler
- Search projection contract endpoint eklendi:
  - `GET /api/admin/search/meili/contract`
- Listing senkron hookları eklendi (event-driven):
  - create/update/publish/unpublish/archive/soft-delete/moderation transition
- Retry queue altyapısı eklendi:
  - `search_sync_jobs` tablosu
  - `pending|processing|retry|done|dead_letter`
  - exponential backoff + max retry + dead-letter
- Queue yönetim endpointleri eklendi:
  - `GET /api/admin/search/meili/sync-jobs`
  - `POST /api/admin/search/meili/sync-jobs/process`
- Bulk reindex endpoint + script eklendi:
  - `POST /api/admin/search/meili/reindex`
  - `backend/scripts/reindex_meili_projection.py`
- Stage doğrulama endpointleri eklendi:
  - `GET /api/admin/search/meili/health`
  - `GET /api/admin/search/meili/stage-smoke`
  - `GET /api/search/meili`

### Teknik Dosyalar
- Backend:
  - `backend/server.py`
  - `backend/app/models/search_sync_job.py`
  - `backend/app/services/meilisearch_index.py`
  - `backend/app/services/meilisearch_config.py` (settings güncellemesi)
  - `backend/scripts/reindex_meili_projection.py`
- Dokümantasyon:
  - `/app/docs/P1_2_LISTING_INDEX_SYNC_EVIDENCE.md`
  - `/app/docs/P1_MEILI_PRODUCTION_RUNBOOK.md`

### Doğrulama
- Testing agent raporu: `/app/test_reports/iteration_14.json`
  - backend 21/21 PASS
  - frontend PASS
- Ek self-test:
  - Hook publish→index add, unpublish→index remove
  - reindex `max_docs=120` ile 100+ doküman testi
  - stage-smoke ranking sort: `premium_score:desc`, `published_at:desc`

### Bilinen Sınır
- Gerçek external Meili URL+key ile stage/prod smoke, admin panelde aktif edilen confige bağlıdır.
- Aktif config yoksa health/reindex/stage-smoke endpointleri fail-fast `ACTIVE_CONFIG_REQUIRED` döner.

---

## 2026-02-26 — External Aktivasyon PASS + P1.3 Facet Başlangıcı

### External Meili Aktivasyonu ve Zorunlu Teknik Doğrulama (PASS)
- External config aktif: `http://217.195.207.70:7700` / `listings_index`
- `GET /api/admin/search/meili/health` → `ok=true` (ACTIVE_CONFIG_REQUIRED yok)
- `GET /api/admin/system/health-detail` → `meili.connected=true`, `status=connected`
- `GET /api/admin/search/meili/stage-smoke?q=` → `200`, hit>0, ranking sort doğrulandı
- `POST /api/admin/search/meili/reindex` + poll sonrası
  - `index_document_count == DB active listing count` (5004)
- Event-driven canlı doğrulama:
  - publish → index add ✅
  - unpublish → index remove ✅
  - soft-delete → index remove ✅
- Retry queue:
  - dead_letter=0, failed=0, metrics healthy

### P1.3 (Facet + Dinamik Sidebar) — Bu turda yapılanlar
- `/api/v2/search` Meili tabanlı facet aggregation ile güncellendi.
- Attribute Manager `filterable=true` alanlar kategori bazlı facet olarak üretiliyor.
- `attr[key]`, `attr[key]_min`, `attr[key]_max` query formatı destekleniyor.
- Facet count’lar Meili aggregation’dan dönüyor (DB fallback yok).
- Frontend `SearchPage` attribute filtrelerini backend’e gönderiyor.
- `FacetRenderer` tarafında `count=0` seçenek disable davranışı aktif.

### Ek Teknik Güncellemeler
- Meili index stats endpoint entegrasyonu (`index_document_count` health/reindex/stage-smoke cevaplarında)
- Filterable attribute güncellemesinde task-completion bekleme eklendi (race condition azaltıldı)
- Dead-letter retry endpoint eklendi:
  - `POST /api/admin/search/meili/sync-jobs/retry-dead-letter`

### Kanıt ve Testler
- Evidence: `/app/docs/P1_2_LISTING_INDEX_SYNC_EVIDENCE.md`
- Runbook: `/app/docs/P1_MEILI_PRODUCTION_RUNBOOK.md`
- Testing agent: `/app/test_reports/iteration_15.json`
  - backend PASS
  - frontend PASS

---

## Değişiklik Geçmişi
- 2026-02-26 sonrası tüm ilerleme notları ve sprint kayıtları:
  - `/app/memory/CHANGELOG.md`
- Admin kapanış kanıt paketi:
  - `/app/docs/ADMIN_CLOSURE_EVIDENCE_PACKAGE_2026-02-26.md`
- Public phase stratejik plan:
  - `/app/memory/PUBLIC_PHASE_STRATEGIC_PLAN.md`

---

## 2026-02-26 — Dealer Dashboard + Manuel Kontrol Sistemi v1 (Tek Paket)

### Teslim Edilenler
- Route haritası tamamlandı:
  - `/dealer/overview`, `/dealer/listings`, `/dealer/messages`, `/dealer/customers`, `/dealer/reports`, `/dealer/purchase`, `/dealer/settings`
- Header hızlı aksiyonları (dealer layout içinde):
  - Favoriler, Mesajlar, İlan Ver, Profil
- Config modeli eklendi:
  - `dealer_nav_items` (header + sidebar)
  - `dealer_modules` (widget registry)
- Global default seed config aktif

### Admin Manuel Kontrol UI
- Sayfa: `/admin/dealer-portal-config`
- dnd-kit ile drag&drop sıralama (nav + module)
- visible toggle
- feature flag read-only gösterim
- dealer önizleme paneli
- audit log kayıtları

### Dealer Portal (Config-Driven)
- Header/sidebar DB config üzerinden render
- Kapalı/yetkisiz item görünmez
- Aktif route highlight doğru
- Draft Mode v1: undo (persist öncesi) + publish + rollback + revision listesi

### Dealer Data & Dashboard
- Tek endpoint: `GET /api/dealer/dashboard/summary`
- In-memory TTL cache v1
- Error contract: `code + message`
- Widget seti click-through ile tamamlandı

### RBAC / Visibility
- Dealer olmayan kullanıcılar `dealer` endpointlerine erişemez
- feature_flag kapalıysa menü/widget görünmez
- Purchase route erişilebilir

### KPI Event Tracking
- `POST /api/analytics/events` dealer eventleriyle entegre edildi:
  - `dealer_nav_click`
  - `dealer_widget_click`
  - `dealer_listing_create_start`
  - `dealer_contact_click`

### Test & Kanıt
- Testing agent raporları: `/app/test_reports/iteration_19.json`, `/app/test_reports/iteration_23.json`, `/app/test_reports/iteration_24.json` (**PASS**)
- Evidence dosyası: `/app/docs/DEALER_DASHBOARD_V1_EVIDENCE.md` + backend test suite `/app/backend/tests/test_p1_dealer_dashboard_bulk_ops.py`, `/app/backend/tests/test_p58_dealer_draft_bulk_async.py`
---
## 2026-02-26 — P0 Kategori Yönetimi Düzeltmesi (Bloklayıcı)

### Durum
- **CLOSED** ✅
- **Internal Milestone:** `CATEGORY_MODULE_STABLE`
- **Category Freeze:** sadece bugfix
### Tamamlanan Kapsam
- `module` standardizasyonu: `real_estate`, `vehicle`, `other`
- Wizard’da `Diğer` + manuel `Sıra` + canlı sıra çakışma önizleme
- Vehicle akışı: serbest metin segment, master data zorunlu eşleşme, country-unique segment kuralı
- Endpointler: `GET /api/admin/categories/vehicle-segment/link-status`, `GET /api/admin/categories/order-index/preview`
### Veri Bütünlüğü / Migration
- Migrationlar: `/app/backend/migrations/versions/p56_category_scope_ordering.py`, `/app/backend/migrations/versions/p57_category_ordering_stabilization.py`
- Scope unique index: `uq_categories_scope_sort` on `(country_code, module, parent_id, sort_order)`
- Migration raporu: `/app/docs/CATEGORY_ORDER_MIGRATION_REPORT.md`

### API Kontratları ve Doğrulama
- Hata kontratı dokümanı: `/app/docs/CATEGORY_API_ERROR_CONTRACTS.md`
- Swagger/OpenAPI response examples: `ORDER_INDEX_ALREADY_USED`, `VEHICLE_SEGMENT_NOT_FOUND`
- Final doğrulama raporları: `/app/test_reports/iteration_22.json`, `/app/test_reports/iteration_23.json`, `/app/test_reports/iteration_24.json` (**PASS**)
