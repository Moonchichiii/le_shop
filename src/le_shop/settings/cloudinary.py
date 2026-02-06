from __future__ import annotations

from typing import Any

import cloudinary
from cloudinary.utils import cloudinary_url as build_cloudinary_url
from decouple import config


def cloudinary_storage_config() -> dict[str, str]:
    cloud_name = config("CLOUDINARY_CLOUD_NAME", default="").strip()
    api_key = config("CLOUDINARY_API_KEY", default="").strip()
    api_secret = config("CLOUDINARY_API_SECRET", default="").strip()

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )

    return {
        "CLOUD_NAME": cloud_name,
        "API_KEY": api_key,
        "API_SECRET": api_secret,
        "MAGIC_FILE_PATH": "magic",
        "PREFIX": "arti_corner/",
    }


def cloudinary_url(
    field: Any,
    width: int,
    aspect_ratio: str = "1:1",
    crop: str = "fill",
) -> str:
    if not field:
        return ""

    public_id = getattr(field, "public_id", field)

    transformation: dict[str, Any] = {
        "fetch_format": "auto",
        "quality": "auto",
        "width": width,
        "crop": crop,
        "aspect_ratio": aspect_ratio,
        "dpr": "auto",
        "flags": "progressive",
        "gravity": "auto",
    }

    url, _ = build_cloudinary_url(public_id, transformation=transformation)
    return url
