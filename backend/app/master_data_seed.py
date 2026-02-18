def default_vehicle_makes(now_iso: str):
    return [
        {
            "id": "make_bmw_de",
            "name": "BMW",
            "slug": "bmw",
            "country_code": "DE",
            "active_flag": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "id": "make_audi_de",
            "name": "Audi",
            "slug": "audi",
            "country_code": "DE",
            "active_flag": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "id": "make_mercedes_de",
            "name": "Mercedes-Benz",
            "slug": "mercedes",
            "country_code": "DE",
            "active_flag": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
    ]


def default_vehicle_models(now_iso: str):
    return [
        {
            "id": "model_bmw_3_series",
            "make_id": "make_bmw_de",
            "name": "3 Series",
            "slug": "3-series",
            "active_flag": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "id": "model_bmw_5_series",
            "make_id": "make_bmw_de",
            "name": "5 Series",
            "slug": "5-series",
            "active_flag": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "id": "model_audi_a4",
            "make_id": "make_audi_de",
            "name": "A4",
            "slug": "a4",
            "active_flag": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "id": "model_mercedes_c_class",
            "make_id": "make_mercedes_de",
            "name": "C-Class",
            "slug": "c-class",
            "active_flag": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
    ]
