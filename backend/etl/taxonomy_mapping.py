"""Specialty taxonomy code mappings (NPI taxonomy -> specialty code)."""

# Map NPI taxonomy codes to internal specialty codes
SPECIALTY_MAPPING: dict[str, str] = {
    "207Q00000X": "primary_care",
    "207R00000X": "primary_care",
    "208D00000X": "primary_care",
    "207RC0000X": "cardiology",
    "207RI0011X": "cardiology",
    "2084N0400X": "neurology",
    "207T00000X": "neurology",
    "207RN0300X": "nephrology",
    "207RX0202X": "oncology",
    "2085R0001X": "oncology",
    "2084P0800X": "psychiatry",
    "2084P0804X": "psychiatry",
    "207V00000X": "obgyn",
    "207X00000X": "orthopedics",
    "208600000X": "general_surgery",
    "207P00000X": "emergency",
    "2085R0202X": "radiology",
    "2085R0205X": "radiology",
    "207ZP0101X": "pathology",
    "207ZP0102X": "pathology",
    "207N00000X": "dermatology",
    "207W00000X": "ophthalmology",
    "208000000X": "pediatrics",
}

SPECIALTY_DISPLAY_NAMES: dict[str, str] = {
    "primary_care": "Primary Care",
    "cardiology": "Cardiology",
    "neurology": "Neurology",
    "nephrology": "Nephrology",
    "oncology": "Oncology",
    "psychiatry": "Psychiatry",
    "obgyn": "OB/GYN",
    "orthopedics": "Orthopedics",
    "general_surgery": "General Surgery",
    "emergency": "Emergency Medicine",
    "radiology": "Radiology",
    "pathology": "Pathology",
    "dermatology": "Dermatology",
    "ophthalmology": "Ophthalmology",
    "pediatrics": "Pediatrics",
}

# Reverse mapping: specialty code -> list of taxonomy codes
SPECIALTY_TAXONOMIES: dict[str, list[str]] = {}
for taxonomy, specialty in SPECIALTY_MAPPING.items():
    SPECIALTY_TAXONOMIES.setdefault(specialty, []).append(taxonomy)
