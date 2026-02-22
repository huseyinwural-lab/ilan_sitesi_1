import { createContext, useContext, useState, useEffect } from 'react';

const translations = {
  tr: {
    // Common
    dashboard: 'Kontrol Paneli',
    users: 'Kullanıcılar',
    countries: 'Ülkeler',
    feature_flags: 'Özellik Bayrakları',
    audit_logs: 'Denetim Kayıtları',
    settings: 'Ayarlar',
    logout: 'Çıkış',
    login: 'Giriş',
    email: 'E-posta',
    password: 'Şifre',
    submit: 'Gönder',
    cancel: 'İptal',
    save: 'Kaydet',
    delete: 'Sil',
    edit: 'Düzenle',
    create: 'Oluştur',
    search: 'Ara',
    filter: 'Filtre',
    all: 'Tümü',
    active: 'Aktif',
    inactive: 'Pasif',
    enabled: 'Etkin',
    disabled: 'Devre Dışı',
    actions: 'İşlemler',
    status: 'Durum',
    name: 'Ad',
    role: 'Rol',
    created_at: 'Oluşturulma',
    updated_at: 'Güncelleme',
    // Dashboard
    total_users: 'Toplam Kullanıcı',
    active_users: 'Aktif Kullanıcı',
    enabled_countries: 'Aktif Ülke',
    enabled_features: 'Aktif Özellik',
    recent_activity: 'Son Aktivite',
    // Roles
    super_admin: 'Süper Admin',
    country_admin: 'Ülke Admin',
    moderator: 'Moderatör',
    support: 'Destek',
    finance: 'Finans',
    // Feature Flags
    module: 'Modül',
    feature: 'Özellik',
    enabled_countries: 'Aktif Ülkeler',
    toggle: 'Aç/Kapa',
    // Auth
    welcome_back: 'Tekrar Hoşgeldiniz',
    login_subtitle: 'Admin paneline erişmek için giriş yapın',
    // Messages
    login_success: 'Giriş başarılı',
    login_error: 'Giriş başarısız',
    save_success: 'Kaydedildi',
    delete_success: 'Silindi',
    // Portals
    portal_consumer: 'Bireysel Portal',
    portal_dealer: 'Ticari Portal',
    nav_section: 'Menü',
    nav_listings: 'İlan Yönetimi',
    nav_favorites: 'Favoriler',
    nav_messages: 'Mesajlar & Bildirimler',
    nav_services: 'Servisler',
    nav_account: 'Hesabım',
    nav_dashboard: 'Özet',
    nav_my_listings: 'İlanlarım',
    nav_create_listing: 'Yeni İlan',
    nav_support: 'Destek Talepleri',
    nav_profile: 'Profil',
    nav_privacy_center: 'Gizlilik Merkezi',
    nav_favorite_listings: 'Favori İlanlar',
    nav_invoices: 'Faturalar',
    nav_company: 'Şirket',
    nav_company_profile: 'Şirket Profili',
    nav_dealer_dashboard: 'Panel',
  },
  de: {
    dashboard: 'Dashboard',
    users: 'Benutzer',
    countries: 'Länder',
    feature_flags: 'Feature Flags',
    audit_logs: 'Audit-Protokolle',
    settings: 'Einstellungen',
    logout: 'Abmelden',
    login: 'Anmelden',
    email: 'E-Mail',
    password: 'Passwort',
    submit: 'Absenden',
    cancel: 'Abbrechen',
    save: 'Speichern',
    delete: 'Löschen',
    edit: 'Bearbeiten',
    create: 'Erstellen',
    search: 'Suchen',
    filter: 'Filter',
    all: 'Alle',
    active: 'Aktiv',
    inactive: 'Inaktiv',
    enabled: 'Aktiviert',
    disabled: 'Deaktiviert',
    actions: 'Aktionen',
    status: 'Status',
    name: 'Name',
    role: 'Rolle',
    created_at: 'Erstellt',
    updated_at: 'Aktualisiert',
    total_users: 'Gesamtbenutzer',
    active_users: 'Aktive Benutzer',
    enabled_countries: 'Aktive Länder',
    enabled_features: 'Aktive Features',
    recent_activity: 'Letzte Aktivität',
    super_admin: 'Super Admin',
    country_admin: 'Länder Admin',
    moderator: 'Moderator',
    support: 'Support',
    finance: 'Finanzen',
    module: 'Modul',
    feature: 'Feature',
    toggle: 'Umschalten',
    welcome_back: 'Willkommen zurück',
    login_subtitle: 'Melden Sie sich an, um auf das Admin-Panel zuzugreifen',
    login_success: 'Erfolgreich angemeldet',
    login_error: 'Anmeldung fehlgeschlagen',
    save_success: 'Gespeichert',
    delete_success: 'Gelöscht',
  },
  fr: {
    dashboard: 'Tableau de bord',
    users: 'Utilisateurs',
    countries: 'Pays',
    feature_flags: 'Flags de fonctionnalités',
    audit_logs: 'Journaux d\'audit',
    settings: 'Paramètres',
    logout: 'Déconnexion',
    login: 'Connexion',
    email: 'E-mail',
    password: 'Mot de passe',
    submit: 'Soumettre',
    cancel: 'Annuler',
    save: 'Enregistrer',
    delete: 'Supprimer',
    edit: 'Modifier',
    create: 'Créer',
    search: 'Rechercher',
    filter: 'Filtrer',
    all: 'Tous',
    active: 'Actif',
    inactive: 'Inactif',
    enabled: 'Activé',
    disabled: 'Désactivé',
    actions: 'Actions',
    status: 'Statut',
    name: 'Nom',
    role: 'Rôle',
    created_at: 'Créé le',
    updated_at: 'Mis à jour',
    total_users: 'Total utilisateurs',
    active_users: 'Utilisateurs actifs',
    enabled_countries: 'Pays actifs',
    enabled_features: 'Fonctionnalités actives',
    recent_activity: 'Activité récente',
    super_admin: 'Super Admin',
    country_admin: 'Admin Pays',
    moderator: 'Modérateur',
    support: 'Support',
    finance: 'Finance',
    module: 'Module',
    feature: 'Fonctionnalité',
    toggle: 'Basculer',
    welcome_back: 'Bon retour',
    login_subtitle: 'Connectez-vous pour accéder au panneau d\'administration',
    login_success: 'Connexion réussie',
    login_error: 'Échec de la connexion',
    save_success: 'Enregistré',
    delete_success: 'Supprimé',
  }
};

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('language') || 'tr';
  });

  useEffect(() => {
    localStorage.setItem('language', language);
  }, [language]);

  const t = (key) => {
    return translations[language]?.[key] || translations.tr[key] || key;
  };

  const getTranslated = (obj) => {
    if (!obj) return '';
    return obj[language] || obj.tr || obj.de || obj.fr || Object.values(obj)[0] || '';
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, getTranslated }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
