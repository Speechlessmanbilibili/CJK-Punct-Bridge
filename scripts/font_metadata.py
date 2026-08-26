VERSION = "1.320"
FONT_REVISION = 1.32
UNIQUE_ID_VENDOR = "SilentPerson"
OS2_VENDOR_ID = "    "

COPYRIGHT = (
    "Portions Copyright 2021 The Hanken Grotesk Project Authors. "
    "Portions Copyright 2014-2021 Adobe, with Reserved Font Name 'Source'. "
    "Portions Copyright 2015 Google Inc. "
    "Portions Copyright 2022 Buernia, with Reserved Font Names 'Zhudou' and '煮豆'. "
    "Modifications copyright 2026 SilentPerson (Speechlessmanbilibili)."
)
TRADEMARK = "Source is a trademark of Adobe in the United States and/or other countries."
MANUFACTURER = "SilentPerson (Speechlessmanbilibili)"
DESIGNER = (
    "SilentPerson (font engineering and integration); Alfredo Marco Pradil "
    "(Hanken Grotesk); Ryoko Nishizuka (kana, bopomofo, and ideographs); "
    "Paul D. Hunt (Latin, Greek, and Cyrillic); Sandoll Communications, "
    "Soo-young Jang, and Joo-yeon Kang (Hangul); Buernia (Zhudou Sans)."
)
DESCRIPTION = (
    "Language-aware punctuation bridge for Simplified Chinese, Traditional Chinese, "
    "Japanese, Korean, and Western text. Built from pinned Google Fonts Noto Sans "
    "SC/TC/JP/KR and Hanken Grotesk sources, with Zhudou-derived CJK dash forms. "
    "Noto CJK production credits: Dr. Ken Lunde (project architecture, glyph-set "
    "definition, and overall production) and Masataka Hattori (production and "
    "ideograph elements)."
)
VENDOR_URL = "https://github.com/Speechlessmanbilibili/CJK-Punct-Bridge"
DESIGNER_URL = "https://github.com/Speechlessmanbilibili"
LICENSE_DESCRIPTION = (
    "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
    "See the bundled OFL.txt and THIRD_PARTY_NOTICES.md for full terms and attribution."
)
LICENSE_URL = "https://openfontlicense.org"

LEGAL_NAMES = {
    0: COPYRIGHT,
    7: TRADEMARK,
    8: MANUFACTURER,
    9: DESIGNER,
    10: DESCRIPTION,
    11: VENDOR_URL,
    12: DESIGNER_URL,
    13: LICENSE_DESCRIPTION,
    14: LICENSE_URL,
}


def project_names(unique_id):
    return {
        **LEGAL_NAMES,
        3: f"{VERSION};{UNIQUE_ID_VENDOR};{unique_id}",
        5: f"Version {VERSION}",
    }


def apply_binary_metadata(font):
    font["OS/2"].achVendID = OS2_VENDOR_ID
    font["head"].fontRevision = FONT_REVISION


def audit_metadata(font, unique_id):
    expected = project_names(unique_id)
    for name_id, value in expected.items():
        record = font["name"].getName(name_id, 3, 1, 0x409)
        assert record is not None, (name_id, "missing Windows English metadata")
        assert record.toUnicode() == value, (name_id, record.toUnicode(), value)
    assert font["OS/2"].achVendID == OS2_VENDOR_ID
    assert font["OS/2"].fsType == 0
    assert abs(font["head"].fontRevision - FONT_REVISION) <= 1 / 65536
