from pathlib import Path
from copy import deepcopy

from fontTools.ttLib import TTCollection
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.scaleUpem import ScalerVisitor


SOURCES = {
    "Pix": (r"C:\Windows\Fonts\msyh_0.ttc", 400, "unhinted"),
    "PixBd": (r"C:\Windows\Fonts\msyhsb.ttc", 600, "compact_vertical_unhinted"),
    "Swat": (r"C:\Windows\Fonts\msyhbd_0.ttc", 700, "glyphs_and_widths_cjk_bounds_unhinted"),
}
OUTPUT_DIR = Path(__file__).resolve().parent / "Fonts"


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


def compact_vertical_metrics(font):
    """Reduce only Windows-facing vertical metrics by the prior 19.3% target."""
    factor = 2182 / 2703
    os2 = font["OS/2"]
    hhea = font["hhea"]
    hhea.ascent = round(hhea.ascent * factor)
    hhea.descent = round(hhea.descent * factor)
    hhea.lineGap = round(hhea.lineGap * factor)
    os2.sTypoAscender = round(os2.sTypoAscender * factor)
    os2.sTypoDescender = round(os2.sTypoDescender * factor)
    os2.sTypoLineGap = round(os2.sTypoLineGap * factor)
    os2.usWinAscent = round(os2.usWinAscent * factor)
    os2.usWinDescent = round(os2.usWinDescent * factor)
    # Legacy Windows controls can take their small-size line box from VDMX.
    for group in font["VDMX"].groups:
        for ppem, (y_max, y_min) in group.items():
            group[ppem] = (round(y_max * factor), round(y_min * factor))


def scale_outlines_only(font, factor):
    """Shrink glyph drawings while deliberately leaving all metrics untouched."""
    glyf = font["glyf"]
    for glyph_name in font.getGlyphOrder():
        glyph = glyf[glyph_name]
        if glyph.isComposite():
            for component in glyph.components:
                component.x = round(component.x * factor)
                component.y = round(component.y * factor)
        elif glyph.numberOfContours > 0:
            glyph.coordinates = GlyphCoordinates(
                [(round(x * factor), round(y * factor)) for x, y in glyph.coordinates]
            )
        glyph.recalcBounds(glyf)
    font.recalcBBoxes = True


def scale_font_uniformly(font, factor=0.5):
    """Scale all layout data together, keeping the original em size."""
    original_upm = font["head"].unitsPerEm
    ScalerVisitor(factor).visit(font)
    font["head"].unitsPerEm = original_upm
    # FontTools scales standard OpenType layout tables, but VDMX needs an
    # explicit matching update for legacy Windows rasterizers.
    for group in font["VDMX"].groups:
        for ppem, (y_max, y_min) in group.items():
            group[ppem] = (round(y_max * factor), round(y_min * factor))


def scale_glyphs_and_widths(font, factor=0.5):
    """Scale drawings and horizontal layout, but restore vertical behavior."""
    original_vdmx = deepcopy(font["VDMX"])
    original_vhea = deepcopy(font["vhea"])
    original_vmtx = deepcopy(font["vmtx"])
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
    font["VDMX"] = original_vdmx
    font["vhea"] = original_vhea
    font["vmtx"] = original_vmtx
    font["hhea"].ascent, font["hhea"].descent, font["hhea"].lineGap = original_hhea
    for field, value in original_os2.items():
        setattr(font["OS/2"], field, value)


def scale_glyphs_and_widths_from_upper_anchor(font):
    """Fit the Bold Chinese top and Latin descender range into y=100..1450."""
    source_bottom = -481
    source_top = 1765
    factor = (1450 - 100) / (source_top - source_bottom)
    scale_glyphs_and_widths(font, factor)
    # The general scaler uses (0, 0) as its origin. Shift the scaled source
    # bottom onto the game's lower visible bound.
    vertical_shift = 100 - round(source_bottom * factor)
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


def remove_truetype_hinting(font):
    """Remove native TrueType hinting and request smoothing without grid fitting."""
    if "glyf" in font:
        for glyph in font["glyf"].glyphs.values():
            glyph.removeHinting()
    for tag in ("cvt ", "fpgm", "prep", "hdmx", "LTSH"):
        if tag in font:
            del font[tag]
    if "maxp" in font and hasattr(font["maxp"], "maxSizeOfInstructions"):
        font["maxp"].maxSizeOfInstructions = 0
    if "gasp" in font:
        # Enable grayscale and symmetric smoothing without grid fitting.
        font["gasp"].gaspRange = {0xFFFF: 0x000A}


def fit_j_hook_inside_advance(font):
    """Move only j's negative-x hook points inside buggy bitmap font cells."""
    glyph_name = font.getBestCmap().get(ord("j"))
    if glyph_name is None:
        return
    glyf = font["glyf"]
    glyph = glyf[glyph_name]
    if glyph.isComposite() or glyph.numberOfContours <= 0:
        return
    left = min(x for x, _ in glyph.coordinates)
    if left >= 0:
        return
    shift = -left
    glyph.coordinates = GlyphCoordinates(
        [(x + shift if x < 0 else x, y) for x, y in glyph.coordinates]
    )
    glyph.recalcBounds(glyf)
    advance, _ = font["hmtx"][glyph_name]
    font["hmtx"][glyph_name] = (advance, glyph.xMin)
    font.recalcBBoxes = True


def scale_glyphs_and_widths_from_descender_anchor(font):
    """Scale to 60% while keeping the g/j/p/q/y descender bottom in place."""
    factor = 0.6
    anchor_y = -482
    scale_glyphs_and_widths(font, factor)
    vertical_shift = round(anchor_y * (1 - factor))
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


def build(name, source, weight, mode):
    font = TTCollection(source).fonts[0]
    if mode == "compact_vertical":
        compact_vertical_metrics(font)
    elif mode == "unhinted":
        fit_j_hook_inside_advance(font)
        remove_truetype_hinting(font)
    elif mode == "compact_vertical_unhinted":
        compact_vertical_metrics(font)
        fit_j_hook_inside_advance(font)
        remove_truetype_hinting(font)
    elif mode == "outline_50":
        scale_outlines_only(font, 0.5)
    elif mode == "outline_70":
        scale_outlines_only(font)
    elif mode == "glyphs_and_widths_50":
        scale_glyphs_and_widths(font)
    elif mode == "glyphs_and_widths_cjk_bounds":
        scale_glyphs_and_widths_from_upper_anchor(font)
    elif mode == "glyphs_and_widths_cjk_bounds_unhinted":
        scale_glyphs_and_widths_from_upper_anchor(font)
        fit_j_hook_inside_advance(font)
        remove_truetype_hinting(font)
    elif mode == "glyphs_and_widths_60_descender":
        scale_glyphs_and_widths_from_descender_anchor(font)
    set_name(font, name)
    font["OS/2"].usWeightClass = weight
    font["OS/2"].fsSelection = font["OS/2"].fsSelection & ~0x61
    if weight >= 700:
        font["OS/2"].fsSelection |= 0x20
        font["head"].macStyle |= 1
    else:
        font["OS/2"].fsSelection |= 0x40
        font["head"].macStyle &= ~1
    font["head"].modified = 0
    output = OUTPUT_DIR / f"{name}.ttf"
    font.save(output)
    return output


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, (source, weight, mode) in SOURCES.items():
        output = build(name, source, weight, mode)
        print(output)


if __name__ == "__main__":
    main()
