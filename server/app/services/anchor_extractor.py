"""Deterministic, local visual-anchor extraction for AnchorReach.

This module is an original implementation for this repository. It does not use
Creative Lab code or data and deliberately does not claim semantic vision-model
understanding. Product appearance is grounded in successfully decoded reference
images and records reproducible image properties for downstream generation and
validation.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image, UnidentifiedImageError

from app.schemas.structured_input import (
    AnchorBlock,
    ExtractionMetadata,
    StructuredCampaignInput,
    VisualAnchors,
)


MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
REMOTE_TIMEOUT_SECONDS = 15.0
REMOTE_IMAGE_HEADERS = {
    "User-Agent": "AnchorReach/0.1 (Open-AI-Design-Agent image validation)",
    "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8",
}


class AnchorExtractionError(ValueError):
    """A blocking image validation or extraction failure."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


@dataclass(frozen=True)
class ParsedImage:
    source: str
    width: int
    height: int
    format: str
    mode: str
    has_transparency: bool
    dominant_colors: tuple[str, ...]


def _is_remote_source(source: str) -> bool:
    return urlparse(source).scheme in {"http", "https"}


async def _read_remote_image(source: str, field: str) -> bytes:
    timeout = httpx.Timeout(REMOTE_TIMEOUT_SECONDS)
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            headers=REMOTE_IMAGE_HEADERS,
        ) as client:
            async with client.stream("GET", source) as response:
                response.raise_for_status()
                declared_size = response.headers.get("content-length")
                if declared_size and int(declared_size) > MAX_IMAGE_BYTES:
                    raise AnchorExtractionError(
                        field,
                        f"image exceeds the {MAX_IMAGE_BYTES // (1024 * 1024)} MB limit",
                    )

                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > MAX_IMAGE_BYTES:
                        raise AnchorExtractionError(
                            field,
                            f"image exceeds the {MAX_IMAGE_BYTES // (1024 * 1024)} MB limit",
                        )
                    chunks.append(chunk)
                return b"".join(chunks)
    except AnchorExtractionError:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        raise AnchorExtractionError(field, f"URL is unreachable: {exc}") from exc


def _read_local_image(source: str, field: str) -> bytes:
    path = Path(source).expanduser()
    if not path.is_file():
        raise AnchorExtractionError(field, f"local file does not exist: {source}")
    try:
        size = path.stat().st_size
        if size > MAX_IMAGE_BYTES:
            raise AnchorExtractionError(
                field,
                f"image exceeds the {MAX_IMAGE_BYTES // (1024 * 1024)} MB limit",
            )
        return path.read_bytes()
    except AnchorExtractionError:
        raise
    except OSError as exc:
        raise AnchorExtractionError(field, f"local file cannot be read: {exc}") from exc


async def _read_image_source(source: str, field: str) -> bytes:
    if _is_remote_source(source):
        return await _read_remote_image(source, field)
    return _read_local_image(source, field)


def _hex_color(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _dominant_colors(image: Image.Image, limit: int = 5) -> tuple[str, ...]:
    rgba = image.convert("RGBA")
    rgba.thumbnail((256, 256), Image.Resampling.LANCZOS)
    pixel_data = (
        rgba.get_flattened_data()
        if hasattr(rgba, "get_flattened_data")
        else rgba.getdata()
    )
    opaque_pixels = [
        (red, green, blue)
        for red, green, blue, alpha in pixel_data
        if alpha >= 32
    ]
    if not opaque_pixels:
        raise ValueError("image has no visible pixels")

    sample = Image.new("RGB", (len(opaque_pixels), 1))
    sample.putdata(opaque_pixels)
    quantized = sample.quantize(colors=limit, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()
    color_counts = quantized.getcolors(maxcolors=limit) or []
    result: list[str] = []
    for _, palette_index in sorted(color_counts, reverse=True):
        offset = palette_index * 3
        color = _hex_color(tuple(palette[offset : offset + 3]))
        if color not in result:
            result.append(color)
    if not result:
        raise ValueError("dominant colors could not be extracted")
    return tuple(result)


def _decode_image(source: str, data: bytes, field: str) -> ParsedImage:
    if not data:
        raise AnchorExtractionError(field, "image is empty")
    try:
        Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            width, height = image.size
            image_format = image.format or "UNKNOWN"
            mode = image.mode
            has_transparency = (
                "A" in image.getbands()
                or "transparency" in image.info
            )
            colors = _dominant_colors(image)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise AnchorExtractionError(field, f"image cannot be parsed: {exc}") from exc

    return ParsedImage(
        source=source,
        width=width,
        height=height,
        format=image_format,
        mode=mode,
        has_transparency=has_transparency,
        dominant_colors=colors,
    )


async def _load_and_decode(source: str, field: str) -> ParsedImage:
    data = await _read_image_source(source, field)
    return _decode_image(source, data, field)


def _build_appearance_description(
    campaign: StructuredCampaignInput,
    images: list[ParsedImage],
) -> str:
    reference_details = []
    for index, image in enumerate(images, start=1):
        transparency = "with transparency" if image.has_transparency else "opaque"
        reference_details.append(
            f"reference {index}: {image.format}, {image.width}x{image.height}, "
            f"{image.mode}, {transparency}, dominant colors "
            f"{', '.join(image.dominant_colors)}"
        )

    product = campaign.product
    return (
        f"{product.brand_name} {product.category}. Preserve the exact silhouette, "
        "proportions, surface details, packaging geometry, and visible brand markings "
        f"shown in {len(images)} decoded product reference image(s). "
        + "; ".join(reference_details)
        + "."
    )


async def build_anchor_block(campaign: StructuredCampaignInput) -> AnchorBlock:
    """Validate every image and build the single source of truth for phase 3."""

    decoded_images: list[ParsedImage] = []
    for index, source in enumerate(campaign.product.images):
        decoded_images.append(
            await _load_and_decode(source, f"product.images.{index}")
        )

    logo_reference = campaign.product.logo_url
    if logo_reference:
        await _load_and_decode(logo_reference, "product.logo_url")

    if campaign.product.primary_color:
        color_palette = [campaign.product.primary_color]
        color_source = "primary_color_field"
    else:
        color_palette = []
        for image in decoded_images:
            for color in image.dominant_colors:
                if color not in color_palette:
                    color_palette.append(color)
                if len(color_palette) == 5:
                    break
            if len(color_palette) == 5:
                break
        if not color_palette:
            raise AnchorExtractionError(
                "product.images",
                "no color anchors could be extracted from the decoded images",
            )
        color_source = "extracted_from_image"

    locked_attributes = ["product_appearance", "color_palette"]
    if logo_reference:
        locked_attributes.insert(1, "logo_reference")

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return AnchorBlock(
        visual_anchors=VisualAnchors(
            product_appearance=_build_appearance_description(campaign, decoded_images),
            logo_reference=logo_reference,
            color_palette=color_palette,
        ),
        locked_attributes=locked_attributes,
        extraction_metadata=ExtractionMetadata(
            source_images_used=[image.source for image in decoded_images],
            color_source=color_source,
            extraction_timestamp=timestamp,
            appearance_extraction_method="deterministic_image_metadata",
        ),
    )
