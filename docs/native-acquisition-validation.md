# Experimental native acquisition validation

This document records observed hardware validation for the experimental native
placement acquisition path. These values are validation evidence for one tested
setup; they are not AcousticBrain scientific thresholds, qualification rules, or
universal measurement constants.

## Observed hardware validation

Tested setup:

- miniDSP UMIK-1 input, resolved as `Umik-1 Gain: 18dB`
- AirPlay stereo output
- UMIK 90 degree calibration file
- 44.1 kHz sample rate
- logarithmic sweep from 20 Hz to 20 kHz
- 5 s sweep duration
- -18 dBFS sweep level
- 1 s pre-silence and 5 s post-silence
- sequence: LEFT A, LEFT B, RIGHT A, RIGHT B

Observed native detection:

- LEFT A: detected at 4.736 s, normalized correlation 0.250, peak/background
  48.0 dB, peak/second 30.1 dB, complete response window
- LEFT B: detected at 4.733 s, normalized correlation 0.250, peak/background
  48.2 dB, peak/second 31.6 dB, complete response window
- RIGHT A: detected at 4.721 s, normalized correlation 0.197, peak/background
  45.1 dB, peak/second 30.1 dB, complete response window
- RIGHT B: detected at 4.723 s, normalized correlation 0.200, peak/background
  45.7 dB, peak/second 27.9 dB, complete response window

Observed AcousticBrain repeatability output for the same run:

- LEFT: 0.87 dB maximum difference at 187.2 Hz,
  `REPEATABILITY_ACCEPTABLE_IN_BAND`
- RIGHT: 1.20 dB maximum difference at 40.4 Hz,
  `REPEATABILITY_ACCEPTABLE_IN_BAND`

## Earlier REW comparison

Earlier experimental comparison between REW exports and native acquisition in
the 40-200 Hz band, after comparable approximate 1/12 smoothing, observed:

- median absolute difference: about 0.41 dB
- P95 absolute difference: about 1.62 dB

These numbers describe an experimental validation run. They must not be used as
contractual acceptance thresholds.

## Limits

The native path is currently experimental. It has been validated as a credible
frequency-response source for the placement journey on the tested setup, but it
does not claim:

- certified absolute SPL accuracy
- absolute timing accuracy over AirPlay
- ETC equivalence with a synchronized audio interface
- absolute phase timing equivalence over AirPlay
- RT60 validation
- distortion validation
- distance estimation from AirPlay delay

The detection thresholds used by the acquisition layer are technical heuristics
for finding a sweep in the recorded signal:

- peak/background >= 12 dB
- peak/second peak >= 6 dB
- normalized correlation >= 0.05

They are not AcousticBrain acoustic quality thresholds and do not affect the
repeatability contract, qualification rules, or scientific verdicts.

## Conclusion

For the tested UMIK-1 plus AirPlay setup, the experimental native acquisition
path is validated as a credible source of frequency-response measurements for
the placement journey. The existing AcousticBrain repeatability and
qualification services remain the authority for repeatability outputs.
