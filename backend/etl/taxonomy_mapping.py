"""Specialty taxonomy code mappings (NPI taxonomy -> specialty code).

Expanded mapping covering ~120 taxonomy codes across 15 specialties.
Source: CMS NUCC Health Care Provider Taxonomy Code Set.
"""

# Map NPI taxonomy codes to internal specialty codes
SPECIALTY_MAPPING: dict[str, str] = {
    # --- Primary Care ---
    "207Q00000X": "primary_care",   # Family Medicine
    "207QA0000X": "primary_care",   # Family Medicine, Adolescent Medicine
    "207QA0505X": "primary_care",   # Family Medicine, Adult Medicine
    "207QG0300X": "primary_care",   # Family Medicine, Geriatric Medicine
    "207QS0010X": "primary_care",   # Family Medicine, Sports Medicine
    "207R00000X": "primary_care",   # Internal Medicine
    "207RA0000X": "primary_care",   # Internal Medicine, Adolescent Medicine
    "207RG0300X": "primary_care",   # Internal Medicine, Geriatric Medicine
    "207RI0200X": "primary_care",   # Internal Medicine, Infectious Disease
    "208D00000X": "primary_care",   # General Practice
    "208M00000X": "primary_care",   # Hospitalist
    "363L00000X": "primary_care",   # Physician Assistant
    "363LA2100X": "primary_care",   # PA, Acute Care
    "363LA2200X": "primary_care",   # PA, Adult Health
    "363LP0200X": "primary_care",   # PA, Primary Care
    "363LF0000X": "primary_care",   # PA, Family Medicine
    "363A00000X": "primary_care",   # PA, Surgical
    "364S00000X": "primary_care",   # Clinical Nurse Specialist
    "363LG0600X": "primary_care",   # PA, Geriatric Medicine
    "261QP2300X": "primary_care",   # Primary Care Clinic

    # --- Cardiology ---
    "207RC0000X": "cardiology",     # Cardiovascular Disease
    "207RI0011X": "cardiology",     # Interventional Cardiology
    "207RC0001X": "cardiology",     # Clinical Cardiac Electrophysiology
    "207RC0200X": "cardiology",     # Critical Care Medicine (Cardiology)
    "207RA0001X": "cardiology",     # Advanced Heart Failure & Transplant
    "207UN0903X": "cardiology",     # Nuclear Cardiology (under Nuclear Med)

    # --- Neurology ---
    "2084N0400X": "neurology",      # Neurology
    "207T00000X": "neurology",      # Neurological Surgery
    "2084N0402X": "neurology",      # Neurology, Child Neurology
    "2084N0600X": "neurology",      # Clinical Neurophysiology
    "2084P0301X": "neurology",      # Brain Injury Medicine
    "2084S0010X": "neurology",      # Sports Medicine (Neurology)
    "2084V0102X": "neurology",      # Vascular Neurology
    "2084P0800X": "neurology",      # Neurology, Psychiatry (dual)
    "2084D0003X": "neurology",      # Neurology, Diagnostic Neuroimaging
    "2084H0002X": "neurology",      # Hospice and Palliative (Neurology)

    # --- Nephrology ---
    "207RN0300X": "nephrology",     # Nephrology
    "207RI0008X": "nephrology",     # Hepatology (related)

    # --- Oncology ---
    "207RX0202X": "oncology",       # Medical Oncology
    "2085R0001X": "oncology",       # Radiation Oncology
    "207RH0003X": "oncology",       # Hematology & Oncology
    "207RH0000X": "oncology",       # Hematology
    "2085H0002X": "oncology",       # Hospice and Palliative (Rad Onc)
    "364SX0106X": "oncology",       # CNS, Oncology
    "207RS0012X": "oncology",       # Surgical Oncology (Surgery subspecialty)

    # --- Psychiatry ---
    "2084P0802X": "psychiatry",     # Addiction Psychiatry
    "2084P0804X": "psychiatry",     # Child & Adolescent Psychiatry
    "2084P0805X": "psychiatry",     # Forensic Psychiatry
    "2084B0040X": "psychiatry",     # Behavioral Neurology & Neuropsychiatry
    "2084F0202X": "psychiatry",     # Forensic Psychiatry (alt)
    "2084P0015X": "psychiatry",     # Psychosomatic Medicine
    "2084A0401X": "psychiatry",     # Addiction Medicine (Psychiatry)
    "2084A2900X": "psychiatry",     # Geriatric Psychiatry

    # --- OB/GYN ---
    "207V00000X": "obgyn",          # Obstetrics & Gynecology
    "207VB0002X": "obgyn",          # Bariatric Medicine (OB/GYN)
    "207VC0200X": "obgyn",          # Critical Care (OB/GYN)
    "207VF0040X": "obgyn",          # Female Pelvic Medicine
    "207VG0400X": "obgyn",          # Gynecologic Oncology
    "207VM0101X": "obgyn",          # Maternal & Fetal Medicine
    "207VX0000X": "obgyn",          # Obstetrics (only)
    "207VX0201X": "obgyn",          # Gynecology (only)
    "207VE0102X": "obgyn",          # Reproductive Endocrinology

    # --- Orthopedics ---
    "207X00000X": "orthopedics",    # Orthopaedic Surgery
    "207XS0114X": "orthopedics",    # Adult Reconstructive Orthopaedic Surgery
    "207XX0004X": "orthopedics",    # Orthopaedic Surgery of the Spine
    "207XS0106X": "orthopedics",    # Orthopaedic Hand Surgery
    "207XS0117X": "orthopedics",    # Orthopaedic Trauma
    "207XX0801X": "orthopedics",    # Orthopaedic Sports Medicine
    "207XP3100X": "orthopedics",    # Pediatric Orthopaedic Surgery
    "207XX0005X": "orthopedics",    # Foot and Ankle Orthopaedics

    # --- General Surgery ---
    "208600000X": "general_surgery", # Surgery
    "2086S0120X": "general_surgery", # Pediatric Surgery
    "2086S0122X": "general_surgery", # Plastic and Reconstructive Surgery
    "2086S0105X": "general_surgery", # Surgery of the Hand
    "2086S0102X": "general_surgery", # Surgical Critical Care
    "2086X0206X": "general_surgery", # Surgical Oncology
    "2086H0002X": "general_surgery", # Hospice and Palliative (Surgery)
    "208G00000X": "general_surgery", # Thoracic Surgery
    "208C00000X": "general_surgery", # Colon & Rectal Surgery
    "204F00000X": "general_surgery", # Transplant Surgery

    # --- Emergency Medicine ---
    "207P00000X": "emergency",       # Emergency Medicine
    "207PE0004X": "emergency",       # Emergency Medical Services
    "207PE0005X": "emergency",       # Undersea & Hyperbaric Medicine
    "207PP0204X": "emergency",       # Pediatric Emergency Medicine
    "207PT0002X": "emergency",       # Medical Toxicology
    "207PS0010X": "emergency",       # Sports Medicine (EM)

    # --- Radiology ---
    "2085R0202X": "radiology",       # Diagnostic Radiology
    "2085R0205X": "radiology",       # Radiation Oncology (dual-mapped)
    "2085R0203X": "radiology",       # Therapeutic Radiology
    "2085D0003X": "radiology",       # Diagnostic Neuroimaging
    "2085N0700X": "radiology",       # Neuroradiology
    "2085P0229X": "radiology",       # Pediatric Radiology
    "2085U0001X": "radiology",       # Nuclear Radiology
    "2085B0100X": "radiology",       # Body Imaging

    # --- Pathology ---
    "207ZP0101X": "pathology",       # Anatomic Pathology
    "207ZP0102X": "pathology",       # Anatomic & Clinical Pathology
    "207ZP0104X": "pathology",       # Chemical Pathology
    "207ZC0006X": "pathology",       # Clinical Pathology
    "207ZP0213X": "pathology",       # Pediatric Pathology
    "207ZN0500X": "pathology",       # Neuropathology
    "207ZB0001X": "pathology",       # Blood Banking & Transfusion
    "207ZD0900X": "pathology",       # Dermatopathology
    "207ZF0201X": "pathology",       # Forensic Pathology
    "207ZH0000X": "pathology",       # Hematology (Pathology)
    "207ZI0100X": "pathology",       # Immunopathology
    "207ZC0500X": "pathology",       # Cytopathology

    # --- Dermatology ---
    "207N00000X": "dermatology",     # Dermatology
    "207ND0101X": "dermatology",     # Dermatopathology
    "207NI0002X": "dermatology",     # Clinical & Lab Dermatological Immunology
    "207NP0225X": "dermatology",     # Pediatric Dermatology
    "207NS0135X": "dermatology",     # Procedural Dermatology

    # --- Ophthalmology ---
    "207W00000X": "ophthalmology",   # Ophthalmology
    "207WX0200X": "ophthalmology",   # Ophthalmic Plastic & Reconstructive Surgery
    "207WX0009X": "ophthalmology",   # Glaucoma Specialist
    "207WX0107X": "ophthalmology",   # Retina Specialist
    "207WX0108X": "ophthalmology",   # Uveitis and Ocular Inflammatory Disease
    "152W00000X": "ophthalmology",   # Optometrist

    # --- Pediatrics ---
    "208000000X": "pediatrics",      # Pediatrics
    "2080A0000X": "pediatrics",      # Adolescent Medicine (Pediatrics)
    "2080C0008X": "pediatrics",      # Child Abuse Pediatrics
    "2080I0007X": "pediatrics",      # Clinical & Lab Immunology (Peds)
    "2080P0006X": "pediatrics",      # Developmental Behavioral Pediatrics
    "2080H0002X": "pediatrics",      # Hospice and Palliative (Peds)
    "2080N0001X": "pediatrics",      # Neonatal-Perinatal Medicine
    "2080P0008X": "pediatrics",      # Pediatric Neurodevelopmental Disabilities
    "2080P0201X": "pediatrics",      # Pediatric Allergy/Immunology
    "2080P0202X": "pediatrics",      # Pediatric Cardiology
    "2080P0203X": "pediatrics",      # Pediatric Critical Care Medicine
    "2080P0204X": "pediatrics",      # Pediatric Emergency Medicine
    "2080P0205X": "pediatrics",      # Pediatric Endocrinology
    "2080P0206X": "pediatrics",      # Pediatric Gastroenterology
    "2080P0207X": "pediatrics",      # Pediatric Hematology-Oncology
    "2080P0208X": "pediatrics",      # Pediatric Infectious Diseases
    "2080P0210X": "pediatrics",      # Pediatric Nephrology
    "2080P0214X": "pediatrics",      # Pediatric Pulmonology
    "2080P0216X": "pediatrics",      # Pediatric Rheumatology
    "2080S0012X": "pediatrics",      # Sleep Medicine (Pediatrics)
    "2080T0004X": "pediatrics",      # Pediatric Transplant Hepatology
    "2080S0010X": "pediatrics",      # Sports Medicine (Peds)
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

# Set of all known taxonomy codes for fast lookup
ALL_TAXONOMY_CODES = frozenset(SPECIALTY_MAPPING.keys())
