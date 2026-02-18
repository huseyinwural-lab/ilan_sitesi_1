from datetime import datetime, timezone


def vehicle_category_tree(now_iso: str | None = None) -> list[dict]:
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()

    root_id = "cat_vehicle_vasita"

    root = {
        "id": root_id,
        "parent_id": None,
        "module": "vehicle",
        "slug": "vasita",
        "name": "Vasıta",
        "icon": "🚗",
        "active_flag": True,
        "country_code": None,
        "sort_order": 0,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    children = [
        ("cat_vehicle_otomobil", "otomobil", "Otomobil", 10),
        ("cat_vehicle_arazi_suv_pickup", "arazi-suv-pickup", "Arazi / SUV / Pickup", 20),
        ("cat_vehicle_motosiklet", "motosiklet", "Motosiklet", 30),
        ("cat_vehicle_minivan_panelvan", "minivan-panelvan", "Minivan / Panelvan", 40),
        ("cat_vehicle_ticari_arac", "ticari-arac", "Ticari Araç", 50),
        ("cat_vehicle_karavan_camper", "karavan-camper", "Karavan / Camper", 60),
        # ("cat_vehicle_elektrikli", "elektrikli", {"tr": "Elektrikli", "de": "Elektrisch", "fr": "Électrique"}, 70),  # removed per request
    ]

    out = [root]
    for cid, slug, name, sort_order in children:
        out.append(
            {
                "id": cid,
                "parent_id": root_id,
                "module": "vehicle",
                "slug": slug,
                "name": name,
                "icon": None,
                "active_flag": True,
                "country_code": None,
                "sort_order": sort_order,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
        )

    return out
