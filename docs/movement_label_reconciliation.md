# Movement-label reconciliation

Correction recorded: 17 September 2026.

## Confirmed movements

The investigator confirmed that Position 4 involved the **right hand touching the left shoulder while the torso twisted left**, and Position 5 was the corresponding opposite-side movement: **left hand touching the right shoulder while the torso twisted right**. Directions refer to the participant's anatomical sides.

| Position | Released CSV identifier | Analysis / manuscript label | Earlier acquisition-code label |
|---|---|---|---|
| 4 | `touch_left_shoulder` | Left shoulder touch and twist | `cross_arms` |
| 5 | `touch_right_shoulder` | Right shoulder touch and twist | `touch_left_shoulder` |

The full eight-position mapping is in the [data dictionary](data_dictionary.md#movement-labels). The short CSV labels name the shoulder touched, not the hand used. They include torso rotation as defined above.

## Correction and provenance

The `POSITION_NAMES` entries and displayed instructions in `code/acquisition/tshirt_ble_protocol.py` were corrected to agree with the released CSVs and the investigator's movement definitions. The preceding acquisition version remains available in [commit 459e8f0](https://github.com/poojasrinivas1304/3d-printed-tpu-smart-tshirt/blob/459e8f09983cd945df7125209a4d207a15367024/code/acquisition/tshirt_ble_protocol.py).

This is a retrospective correction of code labels and documentation, not evidence that this exact acquisition-script version generated the historical recordings. It does not resolve separate differences in acquisition timing or export schema. Historical code and provenance copies in a pinned analysis archive retain their original content; use this correction record when interpreting their earlier movement names.

At the time of the movement-label correction, all rows in the three then-released participant CSVs were checked for agreement between `position_index` and `position_name`. All eight mappings agreed across the files. That label-correction step changed no original recordings, released CSVs, timestamps, numeric class indices, sensor measurements, normalization, validation partitions or classification calculations. The primary analysis already used the correct numeric classes and the labels shown above, so the label correction did not change its numerical results. The later replacement of the public CSV exports is a separate change, documented below.

## Historical CSV version checked during label reconciliation

The following Git blob identifiers refer to the earlier data version available at [commit d0ea9b7](https://github.com/poojasrinivas1304/3d-printed-tpu-smart-tshirt/tree/d0ea9b719da7cabf6b3acbf312914fc7f2f9db13/data/processed). They are historical identifiers, not the current CSV checksums:

- `subject_01.csv`: `aa3c6058da105805ff09dcc564a69d1935a61b09`
- `subject_02.csv`: `98b885bde4d0566574cfff9a123c2660a2242c09`
- `subject_03.csv`: `5e204f30f9f4530676f7a82d9894f7443906cdb2`

## Current supplied CSV exports

The replacement exports were introduced in [commit 899a984](https://github.com/poojasrinivas1304/3d-printed-tpu-smart-tshirt/commit/899a984b25b5ff510d84a702cf7b74f8dc64f4b6). Their Git blob identifiers are:

- `subject_01.csv`: `475e77097760d0642c400b4001deb8e209344a93`
- `subject_02.csv`: `96a096cf6c703cbeed5f615327b741a0c778e00f`
- `subject_03.csv`: `572e1fb108a21adb8a84693af0d4aabad530ed69`

See the [processed-data notes](../data/processed/README.md) for export preparation and rounding differences and the [data dictionary](data_dictionary.md) for the current schema. The historical identifiers above are retained to keep the two data versions distinguishable.
