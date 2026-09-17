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

All rows in the three released participant CSVs were checked for agreement between `position_index` and `position_name`. All eight mappings agree across the files. No original recordings, released CSVs, timestamps, numeric class indices, sensor measurements, normalization, validation partitions or classification calculations were changed. The primary analysis already uses the correct numeric classes and the labels shown above, so its numerical results are unaffected.

The released CSV Git blob identifiers remain:

- `subject_01.csv`: `aa3c6058da105805ff09dcc564a69d1935a61b09`
- `subject_02.csv`: `98b885bde4d0566574cfff9a123c2660a2242c09`
- `subject_03.csv`: `5e204f30f9f4530676f7a82d9894f7443906cdb2`
