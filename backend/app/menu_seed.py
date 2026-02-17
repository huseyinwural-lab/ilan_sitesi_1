from datetime import datetime, timezone


def default_top_menu(now_iso: str | None = None) -> list[dict]:
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()

    allowed = ["DE", "CH", "FR", "AT"]

    # Minimal production menu (locked)
    return [
        {
            "id": "menu_emlak",
            "key": "emlak",
            "name": {"tr": "Emlak", "de": "Immobilien", "fr": "Immobilier"},
            "icon": "🏠",
            "badge": None,
            "sort_order": 10,
            "is_enabled": True,
            "allowed_countries": allowed,
            "required_module": "real_estate",
            "sections": [],
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "id": "menu_vasita",
            "key": "vasita",
            "name": {"tr": "Vasıta", "de": "Fahrzeuge", "fr": "Véhicules"},
            "icon": "🚗",
            "badge": None,
            "sort_order": 20,
            "is_enabled": True,
            "allowed_countries": allowed,
            "required_module": "vehicle",
            "sections": [
                {
                    "id": "sec_vasita_segments",
                    "title": {"tr": "Segmentler", "de": "Segmente", "fr": "Segments"},
                    "links": [
                        {"id": "lnk_otomobil", "label": {"tr": "Otomobil", "de": "Auto", "fr": "Auto"}, "url": "/{country}/vasita/otomobil", "link_type": "internal"},
                        {"id": "lnk_suv", "label": {"tr": "Arazi / SUV / Pickup", "de": "SUV / Pickup", "fr": "SUV / Pickup"}, "url": "/{country}/vasita/arazi-suv-pickup", "link_type": "internal"},
                        {"id": "lnk_moto", "label": {"tr": "Motosiklet", "de": "Motorrad", "fr": "Moto"}, "url": "/{country}/vasita/motosiklet", "link_type": "internal"},
                        {"id": "lnk_van", "label": {"tr": "Minivan / Panelvan", "de": "Van", "fr": "Van"}, "url": "/{country}/vasita/minivan-panelvan", "link_type": "internal"},
                        {"id": "lnk_commercial", "label": {"tr": "Ticari Araç", "de": "Nutzfahrzeug", "fr": "Utilitaire"}, "url": "/{country}/vasita/ticari-arac", "link_type": "internal"},
                        {"id": "lnk_camper", "label": {"tr": "Karavan / Camper", "de": "Wohnmobil", "fr": "Camping-car"}, "url": "/{country}/vasita/karavan-camper", "link_type": "internal"},
                        # {"id": "lnk_ev", "label": {"tr": "Elektrikli", "de": "Elektrisch", "fr": "Électrique"}, "url": "/{country}/vasita/elektrikli", "link_type": "internal"},  # removed per request
                    ],
                }
            ],
            "created_at": now_iso,
            "updated_at": now_iso,
        },
    ]
