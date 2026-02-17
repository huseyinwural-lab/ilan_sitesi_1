from datetime import datetime, timezone


def vehicle_category_tree(now_iso: str | None = None) -> list[dict]:
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()

    allowed = ["DE", "CH", "FR", "AT"]

    def tr(lang: str, name: str, description: str = ""):
        return {"language": lang, "name": name, "description": description}

    root_id = "cat_vehicle_vasita"

    root = {
        "id": root_id,
        "parent_id": None,
        "module": "vehicle",
        "slug": {"tr": "vasita", "de": "vasita", "fr": "vasita"},
        "icon": "🚗",
        "allowed_countries": allowed,
        "is_enabled": True,
        "sort_order": 0,
        "listing_count": 0,
        "translations": [
            tr("tr", "Vasıta"),
            tr("de", "Fahrzeuge"),
            tr("fr", "Véhicules"),
        ],
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    children = [
        ("cat_vehicle_otomobil", "otomobil", {"tr": "Otomobil", "de": "Auto", "fr": "Auto"}, 10),
        ("cat_vehicle_arazi_suv_pickup", "arazi-suv-pickup", {"tr": "Arazi / SUV / Pickup", "de": "SUV / Pickup", "fr": "SUV / Pickup"}, 20),
        ("cat_vehicle_motosiklet", "motosiklet", {"tr": "Motosiklet", "de": "Motorrad", "fr": "Moto"}, 30),
        ("cat_vehicle_minivan_panelvan", "minivan-panelvan", {"tr": "Minivan / Panelvan", "de": "Van", "fr": "Van"}, 40),
        ("cat_vehicle_ticari_arac", "ticari-arac", {"tr": "Ticari Araç", "de": "Nutzfahrzeug", "fr": "Utilitaire"}, 50),
        ("cat_vehicle_karavan_camper", "karavan-camper", {"tr": "Karavan / Camper", "de": "Wohnmobil", "fr": "Camping-car"}, 60),
        # ("cat_vehicle_elektrikli", "elektrikli", {"tr": "Elektrikli", "de": "Elektrisch", "fr": "Électrique"}, 70),  # removed per request
    ]

    out = [root]
    for cid, slug, names, sort_order in children:
        out.append(
            {
                "id": cid,
                "parent_id": root_id,
                "module": "vehicle",
                "slug": {"tr": slug, "de": slug, "fr": slug},
                "icon": None,
                "allowed_countries": allowed,
                "is_enabled": True,
                "sort_order": sort_order,
                "listing_count": 0,
                "translations": [
                    tr("tr", names["tr"]),
                    tr("de", names["de"]),
                    tr("fr", names["fr"]),
                ],
                "created_at": now_iso,
                "updated_at": now_iso,
            }
        )

    return out
