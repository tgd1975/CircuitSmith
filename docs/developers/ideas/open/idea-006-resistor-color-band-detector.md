---
id: IDEA-006
title: Resistor color band detector (spinoff tool)
description: Spinoff tool: identify resistor values from photo color bands and verify uniform value across image
category: 🛠️ tooling
---

A small standalone utility — sibling to CircuitSmith rather than core to it —
that takes a photograph of one or more through-hole resistors and reports the
nominal resistance value of each, plus a sanity flag if the image is supposed
to contain a uniform batch but doesn't.

## Motivation

Bench workflows around CircuitSmith and PartsLedger involve a lot of loose
resistors fished out of mixed bins. The colour-band code is unambiguous in
theory but painful in practice — small bands, poor lighting, ambiguous
red/orange/brown, and faded gold/silver tolerance bands. A tool that turns a
phone photo into "this is a 4.7 kΩ ±5 % resistor" would shave real friction
off PartsLedger inventory entry and CircuitSmith bench-testing.

The "are these all the same value?" check covers a second concrete failure
mode: a batch of resistors sold or kitted as one value but actually mixed.
Catching that visually before they go into a board is much cheaper than
debugging the assembled circuit.

## Two modes

The tool ships in two flavours sharing the same decoding core:

1. **Still-image mode (V1).** User takes a photo on demand (phone, webcam,
   scanner), feeds it to the tool, gets a report. Single-shot, batch-friendly,
   no realtime constraint. Classical CV is probably sufficient here — the
   pipeline can afford to be slow and thorough on one frame.
2. **Live-view mode (V2).** A camera feed (laptop webcam, phone-as-webcam,
   Pi camera) is processed in realtime with an on-screen overlay showing the
   decoded value next to each visible resistor. Useful at the bench: pick up
   a resistor, hold it to the camera, see the value. The realtime constraint
   (≥10 fps on commodity hardware) and the need to handle motion blur and
   varying focus distance push this toward a small trained detector + band
   classifier rather than pure HSV thresholding — i.e. **PyTorch is
   probably unavoidable** for V2, whereas V1 can stay dependency-light.

V1 should ship first; V2 is a separate effort built on V1's decoding
primitives.

## Scope (rough)

In scope (V1, still-image):

- Single image input (phone photo, scanner, etc.) containing one or more
  through-hole axial resistors.
- 4-band and 5-band color codes; ±tolerance band detection.
- Per-resistor output: nominal value, tolerance, confidence score.
- Batch-uniformity check: report `uniform` / `mixed` plus which resistors
  deviate.

In scope (V2, live-view), additionally:

- Webcam / video-stream input at ≥10 fps on commodity laptop hardware.
- On-screen overlay: bounding box + decoded value per visible resistor.
- Stable decoding across frames (no flicker between candidate values when
  the resistor is held still).

Out of scope (for both versions, first cut):

- SMD resistors (numeric markings, completely different problem).
- AR / phone-app packaging — V2 is desktop-first.
- Integration with PartsLedger as a write-path (inventory entry stays manual
  for now; this tool just *reports* the value).

## Rough approach

Two halves, roughly independent:

1. **Resistor localisation.** Segment the image into bounding boxes around
   each resistor body.
   - V1: classical CV (HSV thresholding on the typical beige/blue body,
     contour finding) probably works on a still photo with reasonable
     framing.
   - V2: a small trained detector (YOLO-nano, MobileNet-SSD, or similar)
     run via PyTorch — the realtime + cluttered-bench + motion-blur
     combination makes the classical approach too brittle.
2. **Band reading.** Within each resistor's box, find the band positions
   along the body axis, sample each band's dominant colour, and classify
   against the EIA colour table. Orientation ambiguity (which end is band 1?)
   is resolved by checking which decoding produces an E-series-compliant
   value; ties get flagged as low-confidence. This stage is shared between
   V1 and V2 — same decoder, different upstream localisation.

Once each resistor has a decoded value + confidence, the uniformity check is
trivial: cluster the values, flag any cluster smaller than `n - 1`. (In V2,
this becomes "are all *currently visible* resistors the same value?".)

## Open questions

- **Spinoff repo or sub-package?** It's not really a CircuitSmith feature —
  CircuitSmith is schematic generation, not vision. Probably belongs in its
  own small repo (`resistor-reader`?) that PartsLedger and CircuitSmith can
  both call. Decide before any implementation work.
- **Calibration card?** A small printed reference card with known
  colour swatches placed in-frame would eliminate the white-balance problem
  entirely. Optional, but the difference between "phone photo under kitchen
  light" and "phone photo with a calibration card" is enormous.
- **Confidence threshold for `uniform` claim.** A single low-confidence
  outlier in a batch of 20 shouldn't fail the uniformity check. Probably
  cluster on value-with-confidence-weighting rather than raw value.
- **Relationship to [[idea-005-partsledger-inventory-as-input]].** If this
  matures, it could feed PartsLedger inventory entries — but only after
  PartsLedger has a write API the tool can call. Keep them independent for
  now.
