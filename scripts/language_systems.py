"""OpenType language-system policy shared by builds and release audits.

Tags use Microsoft's OpenType 1.9 registry. They are grouped by the Western
script in which this font can supply Hanken punctuation. The set covers the
project's locales, common modern/historic Western locales, and every explicit
language system present in the pinned Google Fonts Hanken Grotesk source.

Only explicit language records use this policy, including explicit languages
for Common-script (`DFLT`) punctuation/number runs. Every default LangSys
remains Noto SC, and East-Asian tags stay on their corresponding Noto region.
"""

def _tags(value):
    return tuple(sorted(tag.ljust(4) for tag in value.split()))


_SCRIPT_LANGUAGE_SYSTEMS = {
    "latn": _tags("""
        AFK ALS ANG AST AZE BOS BRE CAT COR COS CRT CSB CSY DAN DEU ENG ESP ETI
        EUQ FIN FLE FRA FRC FRI FRL FRP GAE GAG GAL HRV HUN IDO ILE INA IND IRI
        IRT ISL ITA JBO KAZ LAD LAT LTH LTZ LVI MAH MLY MOL NDS NLD NOR NOV NSM NTO
        NYN OCI PLK PTG ROM SCO SKY SLV SQI SRB SVE SWK TAT TRK VIT VOL VRO WEL WLN
        ZEA
    """),
    "cyrl": _tags("""
        ABA ABK ADY ALT AVR BAL BEL BGR BSH CHE CHU CRT DAR ERZ HMA ING KAB KAR
        KAZ KIR KOM KOP KOZ KRK KRL KRM KUM LAK LEZ LMA MKD MNG MOK MONT OSS
        RUS SRB TAJ TAT TUV UDM UKR YAK
    """),
    "grek": _tags("ELL PGR"),
}
WESTERN_LANGUAGE_TAGS = tuple(sorted({
    tag for tags in _SCRIPT_LANGUAGE_SYSTEMS.values() for tag in tags
}))
WESTERN_LANGUAGE_SYSTEMS = {
    "DFLT": WESTERN_LANGUAGE_TAGS,
    **_SCRIPT_LANGUAGE_SYSTEMS,
}
WESTERN_SCRIPT_TAGS = tuple(WESTERN_LANGUAGE_SYSTEMS)

CJK_LANGUAGE_ALIASES = {
    "SC": ("ZHS ", "ZHP "),
    "TC": ("ZHT ", "ZHH ", "ZHTM"),
    "JP": ("JAN ",),
    "KR": ("KOR ", "KOH "),
}
CJK_LANGUAGE_TAGS = frozenset(
    tag for aliases in CJK_LANGUAGE_ALIASES.values() for tag in aliases
)

# Punctuation code points present in both the bridge repertoire and the pinned
# Google Fonts Hanken Grotesk source. Build-time checks recompute this set and
# fail if the pinned inputs drift.
HANKEN_SHARED_PUNCTUATION = (
    0x0021, 0x0022, 0x0023, 0x0025, 0x0026, 0x0027, 0x0028, 0x0029,
    0x002A, 0x002C, 0x002E, 0x002F, 0x003A, 0x003B, 0x003F, 0x0040,
    0x005B, 0x005C, 0x005D, 0x005F, 0x007B, 0x007D, 0x00A1, 0x00A7,
    0x00AB, 0x00B6, 0x00B7, 0x00BB, 0x00BF, 0x2013, 0x2014, 0x2015,
    0x2018, 0x2019, 0x201A, 0x201C, 0x201D, 0x201E, 0x2020, 0x2021,
    0x2022, 0x2025, 0x2026, 0x2030, 0x2039, 0x203A,
)
