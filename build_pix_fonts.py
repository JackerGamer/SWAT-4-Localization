from copy import deepcopy
from functools import cache
import os
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.scaleUpem import ScalerVisitor


LOCAL_FONT_DIR = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts"
OUTPUT_DIR = Path(__file__).resolve().parent / "Fonts"
LOCALIZATION_DIR = Path(__file__).resolve().parent / "Simplified Chinese"
SWAT_TARGET_BOUNDS = (0, 700)


def set_name(font, name):
    """Replace visible family/name records with a single predictable name."""
    name_table = font["name"]
    for record in list(name_table.names):
        if record.nameID in {1, 2, 3, 4, 6, 16, 17}:
            name_table.names.remove(record)
    # Name IDs 1/4/6 are the family, full, and PostScript-facing names.  Each
    # file is intentionally a standalone family so its requested name appears
    # unchanged in font menus.
    for platform, encoding, language in ((3, 1, 0x0409), (3, 1, 0x0804)):
        name_table.setName(name, 1, platform, encoding, language)
        name_table.setName("Regular", 2, platform, encoding, language)
        name_table.setName(f"OpenAI:{name}:1.0", 3, platform, encoding, language)
        name_table.setName(name, 4, platform, encoding, language)
        name_table.setName(name, 6, platform, encoding, language)
        name_table.setName(name, 16, platform, encoding, language)
        name_table.setName("Regular", 17, platform, encoding, language)


@cache
def get_localization_characters():
    """Load the unique characters used by all Simplified Chinese resources."""
    characters = set()
    for path in LOCALIZATION_DIR.rglob("*.sch"):
        characters.update(path.read_text(encoding="utf-16"))
    if not characters:
        raise ValueError(f"No characters found in {LOCALIZATION_DIR}")
    return frozenset(characters)


def get_localization_vertical_bounds(font):
    """Return the ink bounds of every supported character used by the game."""
    cmap = font.getBestCmap()
    glyf = font["glyf"]
    bounds = []
    for character in get_localization_characters():
        glyph_name = cmap.get(ord(character))
        if glyph_name is None:
            continue
        glyph = glyf[glyph_name]
        if glyph.numberOfContours == 0 and not glyph.isComposite():
            continue
        glyph.recalcBounds(glyf)
        bounds.append((glyph.yMin, glyph.yMax))
    if not bounds:
        raise ValueError(f"No supported characters found in {LOCALIZATION_DIR}")
    return min(y_min for y_min, _ in bounds), max(y_max for _, y_max in bounds)


def compact_vertical_metrics(font):
    """Set the smallest metrics that contain every localization glyph."""
    ink_bottom, ink_top = get_localization_vertical_bounds(font)
    os2 = font["OS/2"]
    hhea = font["hhea"]

    hhea.ascent = ink_top
    hhea.descent = ink_bottom
    hhea.lineGap = 0
    os2.sTypoAscender = hhea.ascent
    os2.sTypoDescender = hhea.descent
    os2.sTypoLineGap = hhea.lineGap
    os2.usWinAscent = hhea.ascent
    os2.usWinDescent = -hhea.descent
    os2.fsSelection |= 0x80  # USE_TYPO_METRICS


def scale_glyphs_and_widths(font, factor):
    """Scale drawings and horizontal layout, but restore vertical behavior."""
    original_vdmx = deepcopy(font["VDMX"]) if "VDMX" in font else None
    original_vhea = deepcopy(font["vhea"]) if "vhea" in font else None
    original_vmtx = deepcopy(font["vmtx"]) if "vmtx" in font else None
    hhea = font["hhea"]
    original_hhea = (hhea.ascent, hhea.descent, hhea.lineGap)
    os2 = font["OS/2"]
    vertical_fields = (
        "ySubscriptXSize", "ySubscriptYSize", "ySubscriptXOffset", "ySubscriptYOffset",
        "ySuperscriptXSize", "ySuperscriptYSize", "ySuperscriptXOffset", "ySuperscriptYOffset",
        "yStrikeoutSize", "yStrikeoutPosition", "sTypoAscender", "sTypoDescender",
        "sTypoLineGap", "usWinAscent", "usWinDescent", "sxHeight", "sCapHeight",
    )
    original_os2 = {field: getattr(os2, field) for field in vertical_fields if hasattr(os2, field)}
    original_upm = font["head"].unitsPerEm
    ScalerVisitor(factor).visit(font)
    font["head"].unitsPerEm = original_upm
    if original_vdmx is not None:
        font["VDMX"] = original_vdmx
    if original_vhea is not None:
        font["vhea"] = original_vhea
    if original_vmtx is not None:
        font["vmtx"] = original_vmtx
    font["hhea"].ascent, font["hhea"].descent, font["hhea"].lineGap = original_hhea
    for field, value in original_os2.items():
        setattr(font["OS/2"], field, value)


def fit_localization_to_swat_bounds(font):
    """Fit every localization glyph into y=0..700."""
    source_bottom, source_top = get_localization_vertical_bounds(font)
    target_bottom, target_top = SWAT_TARGET_BOUNDS
    factor = (target_top - target_bottom) / (source_top - source_bottom)
    scale_glyphs_and_widths(font, factor)
    # The general scaler uses (0, 0) as its origin. Shift the scaled source
    # bottom onto the game's lower visible bound.
    vertical_shift = target_bottom - round(source_bottom * factor)
    glyf = font["glyf"]
    for glyph_name in font.getGlyphOrder():
        glyph = glyf[glyph_name]
        if not glyph.isComposite() and glyph.numberOfContours > 0:
            glyph.coordinates = GlyphCoordinates(
                [(x, y + vertical_shift) for x, y in glyph.coordinates]
            )
            glyph.recalcBounds(glyf)
    for glyph_name in font.getGlyphOrder():
        if glyf[glyph_name].isComposite():
            glyf[glyph_name].recalcBounds(glyf)
    font.recalcBBoxes = True
    actual_bottom, actual_top = get_localization_vertical_bounds(font)
    if (actual_bottom, actual_top) != (target_bottom, target_top):
        raise ValueError(
            "Scaled localization bounds are "
            f"{actual_bottom}..{actual_top}, expected {target_bottom}..{target_top}"
        )

FONT_SPECS = (
    ("Pix", LOCAL_FONT_DIR / "MiSans-Regular.ttf", 400, compact_vertical_metrics),
    ("PixBd", LOCAL_FONT_DIR / "MiSans-Demibold.ttf", 600, compact_vertical_metrics),
    ("Swat", LOCAL_FONT_DIR / "MiSans-Bold.ttf", 700, fit_localization_to_swat_bounds),
)


def build(name, source, weight, transform):
    font = TTFont(source, recalcTimestamp=False)
    transform(font)
    set_name(font, name)
    font["OS/2"].usWeightClass = weight
    font["OS/2"].fsSelection = font["OS/2"].fsSelection & ~0x61
    if weight >= 700:
        font["OS/2"].fsSelection |= 0x20
        font["head"].macStyle |= 1
    else:
        font["OS/2"].fsSelection |= 0x40
        font["head"].macStyle &= ~1
    font["head"].modified = font["head"].created
    output = OUTPUT_DIR / f"{name}.ttf"
    font.save(output)
    return output


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, source, weight, transform in FONT_SPECS:
        output = build(name, source, weight, transform)
        print(output)


if __name__ == "__main__":
    main()
