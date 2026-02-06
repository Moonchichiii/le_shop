from __future__ import annotations

from le_shop.settings.cloudinary import cloudinary_url


def cloudinary_helpers() -> dict[str, object]:
    return {"cloudinary_url": cloudinary_url}
