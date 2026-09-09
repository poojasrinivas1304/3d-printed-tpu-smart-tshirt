# Ethics and data-release statement

## Confirmed manuscript information

- Khalifa University protocol: **H26-049**.
- Approval date: **2 September 2026**.
- Data-collection date: **3 September 2026**.
- Written informed consent was obtained from every participant before participation.
- Public sharing is limited to the de-identified sensor measurements in `data/processed/`. Ethics correspondence, signed consent forms, and the participant identity key are controlled study records and are not public repository materials.

## Acquisition-clock correction

The source workbooks contained June 2026 calendar timestamps because the acquisition computer's calendar was incorrect. The recordings were collected on 3 September 2026.

The original workbooks remain unchanged outside the repository. Corrected audit copies preserve the original file checksum, recorded date, applied offset, and correction rationale. Public CSVs assign S01–S03, remove the direct-name row, replace the erroneous calendar date with 3 September 2026, preserve relative timing and sensor measurements, and omit absolute Unix timestamps. See `date_correction_log.md`.

## Public-release scope

The public CSVs contain posture-protocol labels and sensor measurements only. They exclude names, initials, contact information, medical information, device and network addresses, the participant identity key, signed consent documentation, and absolute Unix timestamps. Public identifiers S01–S03 are repository-specific codes and are not derived from participant names.
