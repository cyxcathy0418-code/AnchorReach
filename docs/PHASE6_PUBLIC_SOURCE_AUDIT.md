# AnchorReach Phase 6: Public Source and License Audit

Verified on 2026-08-04 for the frozen `phase6_protocol_v1` holdout design.

## Outcome

- 12 product sources and eight separate Logo sources are selected.
- All 20 evaluation URLs downloaded successfully and decoded as JPEG or PNG.
- Each product source was visually checked against its frozen category.
- All sources are publicly accessible through Wikimedia Commons. Creative Lab code and data were not used.
- No API generation or model judging was performed, so this audit cost USD 0.

The machine-readable source of truth is `docs/evaluation/phase6_public_sources.json`. It records each author, file page, evaluation URL, license, original SHA-1, evaluated dimensions, decode result, and trademark note.

## Product sources

| Slot | Category | Selected Commons file | License | Visual / trademark note |
| --- | --- | --- | --- | --- |
| P01 | reusable bottle | [Stainless Steel Water Bottle](https://commons.wikimedia.org/wiki/File:Stainless_Steel_Water_Bottle.jpg) | CC BY-SA 4.0 | Unbranded reusable metal bottle. |
| P02 | skin-care bottle | [Eye Dropper Bottle 1](https://commons.wikimedia.org/wiki/File:Eye_Dropper_Bottle_1.jpg) | CC0 1.0 | Clean generic dropper bottle. |
| P03 | wireless earbuds | [Беспроводные наушники](https://commons.wikimedia.org/wiki/File:%D0%91%D0%B5%D1%81%D0%BF%D1%80%D0%BE%D0%B2%D0%BE%D0%B4%D0%BD%D1%8B%D0%B5_%D0%BD%D0%B0%D1%83%D1%88%D0%BD%D0%B8%D0%BA%D0%B8.jpg) | CC0 1.0 | EDIFIER/X5 markings visible; local evaluation only. |
| P04 | running shoe | [Running shoes](https://commons.wikimedia.org/wiki/File:Running_shoes.jpg) | CC BY-SA 4.0 | Clean white-background pair; ASICS marks visible. |
| P05 | backpack | [School bag backpack](https://commons.wikimedia.org/wiki/File:School_bag_backpack.jpg) | CC BY-SA 3.0 | Clear backpack; GRIP label treated as a possible mark. |
| P06 | wristwatch | [Wristwatch](https://commons.wikimedia.org/wiki/File:Wristwatch.jpg) | Public domain | Full watch face; SEASIDE wording visible. |
| P07 | coffee maker | [Drip coffee maker](https://commons.wikimedia.org/wiki/File:Drip_coffee_maker.svg) | CC0 1.0 | Unbranded illustration; rasterized to PNG for decoder compatibility. |
| P08 | snack package | [Popcorn](https://commons.wikimedia.org/wiki/File:Popcorn.svg) | CC0 1.0 | Generic popcorn carton; rasterized to PNG. |
| P09 | camera | [Kodak Instamatic X-15 camera](https://commons.wikimedia.org/wiki/File:Kodak_Instamatic_X-15_camera.jpg) | CC0 1.0 | Kodak/Instamatic marks visible; local evaluation only. |
| P10 | desk lamp | [Black desk lamp](https://commons.wikimedia.org/wiki/File:Black_desk_lamp.jpg) | CC0 1.0 | Clear unbranded lamp silhouette. |
| P11 | hand tool | [Cordless electric drill](https://commons.wikimedia.org/wiki/File:Cordless_electric_(screw)_drill.jpg) | CC0 1.0 | BLACK & DECKER mark visible; local evaluation only. |
| P12 | perfume bottle | [Perfume Bottle](https://commons.wikimedia.org/wiki/File:Perfume_Bottle.jpg) | Public domain | Generic unbranded glass bottle. |

## Logo sources and assignments

| Logo | Product slot | Selected Commons file | Copyright license | Trademark boundary |
| --- | --- | --- | --- | --- |
| L01 | P01 | [Wikimedia logo](https://commons.wikimedia.org/wiki/File:Wikimedia-logo.svg) | Public domain / copyright-ineligible | Official Wikimedia mark; local evaluation only. |
| L02 | P02 | [Debian OpenLogo](https://commons.wikimedia.org/wiki/File:Debian_logo.png) | Swirl: LGPL-3.0+ or CC BY-SA 3.0; text PD | Debian trademark; local evaluation only. |
| L03 | P03 | [Python logo and wordmark](https://commons.wikimedia.org/wiki/File:Python_logo_and_wordmark.svg) | GPL-2.0+ | Python trademark; PSF policy applies. |
| L04 | P04 | [Blender logo and wordmark](https://commons.wikimedia.org/wiki/File:Logo_Blender.svg) | Public-domain textlogo | Blender trademark; local evaluation only. |
| L05 | P05 | [Git logo and wordmark](https://commons.wikimedia.org/wiki/File:Git-logo.svg) | CC BY 3.0 | Git trademark; credit Jason Long. |
| L06 | P06 | [Inkscape logo](https://commons.wikimedia.org/wiki/File:Inkscape_Logo.svg) | CC BY-SA 3.0 / GPL-2.0+ | Inkscape trademark; local evaluation only. |
| L07 | P07 | [VLC icon](https://commons.wikimedia.org/wiki/File:VLC_icon.png) | GPL-2.0+ | Treat as protected identity; local evaluation only. |
| L08 | P08 | [Firefox logo (2019)](https://commons.wikimedia.org/wiki/File:Firefox_logo,_2019.svg) | MPL 2.0 | Firefox trademark; Mozilla rules apply. |

## Compliance boundary

This audit verifies public accessibility, file-page licensing statements, attribution/share-alike flags, image decoding, and category fit. It does not grant commercial trademark permission and is not legal advice. Trademark-bearing sources are acceptable only because the current purpose is a frozen local technical benchmark. Any public release, marketing use, or dataset distribution must receive a new rights review and include required attribution and share-alike notices.

## Changes made after visual QA

The first selection pass was not accepted blindly. Four candidates were replaced before freezing sources: a disposable plastic bottle, a mislabeled backpack file whose downloaded image showed a forest, a footwear photo with people and multiple shoe types, and a cluttered grocery-bag photo. The replacements above reduce reference ambiguity before scores are collected.
