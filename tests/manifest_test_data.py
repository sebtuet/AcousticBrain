def future_manifest_extension():
    return {
        "revision": 7,
        "enabled": True,
        "nullable": None,
        "labels": ["alpha", "beta"],
        "nested": {
            "threshold": 0.125,
            "metadata": {
                "owner": "future-component",
            },
        },
    }
