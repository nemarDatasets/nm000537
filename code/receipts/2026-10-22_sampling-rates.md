# Receipt: measured sampling rate of every run

**Claim**: sub-400: sampling rate 16000 Hz, not 8000; rate basis measured (v1.0.3)

## Source
- OSF dngv5 release (Oya & LeiQi, doi:10.17605/OSF.IO/DNGV5): the 46 `<PT>/<run>/EPdata3D.mat` files (`EP_data3D`,
  trials x samples x 256 channel slots), sha256 listed at the end.
- Identity with NEMAR: for every run the script rebuilds the `_ieeg.eeg` bytes as `code/cv6_conv_lit165.py` writes them
  (channel slots with data, epochs back to back, little-endian float32); their sha256 equals the `SHA256E` git-annex key
  of the run's `_ieeg.eeg` at `origin/main` `d46e41a6c50c42d36c8e7557d8f14691d866815b` (46/46, column `eeg = annex key`).
- NEMAR text files read: `_ieeg.json`, `_channels.tsv`, `_events.tsv` of the 46 runs at
  `43ea23a8dee54c6878bff876f07ddfc878064d7d` (this PR's data commit; unchanged at the PR head).
- The annexed `.vhdr` of the 9 runs whose rate differs from 8000 Hz (sub-369 runs 91/92, sub-400, sub-515), fetched from
  `nemar-s3` (sha256 equal to their annex keys; checked by hand, not by the script), all say `SamplingInterval=125.0`
  (8000 Hz).

## Method
- Script: `2026-10-22_sampling-rates.py <release_root> <nm000537_checkout>` (numpy 2.5.4, scipy 1.18.1, pandas 3.1.0),
  run on Slurm. Reader: `scipy.io.loadmat`; values used as stored (no scaling). Centre sample c = (n - 1) / 2 of an
  n-sample epoch.
- Mains comb: pre-stimulus baseline = samples [0, c - max(n/80, 160)) of every trial x channel slot with no NaN and
  |x| < 0.98 x the run's maximum |x|; linear detrend, Hann window, zero-padded FFT (8x), power averaged; ratio = power /
  median-filtered background (0.006 cycle/sample). Comb ratio at f Hz for a candidate rate = largest ratio within
  +/- the Hann main lobe of f / rate cycle/sample; score = median over 60/180/300/420/540 Hz. Candidates: 2000, 4000,
  8000, 16000, 24000, 32000 Hz and the TDT-style 2034.5, 4069, 8138, 16276, 24414 Hz; best = highest score.
- Fitted rate: peaks (ratio >= 5, parabolic interpolation) at the 60 Hz harmonics k up to min(0.45 x best, 2000 Hz);
  weighted least squares of the peak frequencies on k (weight log10 ratio) gives the fundamental in cycle/sample;
  rate = 60 Hz / fundamental, with its standard error. In sub-369 run 100 (short baseline) the comb scores 8000 and
  8138 Hz alike; the fit separates them.
- Harmonics present: 60 Hz multiples up to 0.49 cycle/sample at the best rate with ratio >= 5 (highest one, odd/even
  counts).
- Roll-off: frequency of the steepest fall of the smoothed log background between 0.03 and 0.47 cycle/sample.
- Stimulus-artefact spectrum: +/-512 samples around c, per-trial median of the first 256 samples removed, trial polarity
  aligned to the mean of the central 17 samples (5 iterations), trial mean per channel. Channels used: never reaching
  0.98 x the run's maximum |x| in that window, no NaN, peak in the central 17 samples > 20 x the SD of the first 256
  samples. Hann window of +/-128 samples, power spectrum (4096-point FFT) normalised per channel to its 0.005-0.24
  cycle/sample sum, median over channels; drop = 10 log10(power at 0.16 / power at 0.24 cycle/sample). A 0.2 ms/phase biphasic pulse is
  3.2 samples per phase at 16 kHz (spectral null at 0.31 cycle/sample) and 1.6 samples at 8 kHz (null above Nyquist).
- Lock: per epoch, channels with no NaN; profile = median over channels of |x[i+1] - x[i]|, without the step into the
  last sample. Centre ratio = profile maximum within +/-20 samples of c / profile median; artefact at centre if
  ratio >= 10. Sharpest jump at centre: profile maximum within +/-20 samples of c.
- Padding: count of finite values equal to 0 in the last sample of each epoch (second-to-last sample as control).
- NaN trial x channel: fraction of (epoch, channel) pairs with NaN, over the channels kept in BIDS.
- BIDS fields consistent: channels.tsv rows = channel slots with data and `sampling_frequency` = `SamplingFrequency`;
  `EpochLength` = n / rate, `RecordingDuration` = epochs x n / rate (|diff| < 1e-9 s); one event per epoch at sample
  k x n + constant; onset = sample / rate (|diff| < 1e-9 s).

## Result
Mains comb, fitted rate and the BIDS fields at `43ea23a`:

| run | epochs | samples/epoch | comb median @2 kHz | comb median @8 kHz | comb median @16 kHz | best rate (Hz) | runner-up (Hz, score) | comb @best 60/180/300/420/540 | fit (Hz) | fit SE (Hz) | harmonics fitted | highest harmonic (Hz) | odd/even harmonics present | roll-off (cycle/sample) | BIDS SamplingFrequency | BIDS fields consistent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 369/91 | 60 | 4001 | 51.9 | 1.0 | 1.0 | 2000 | 2034.5 (1.9) | 51.9/172.4/57.2/29.1/7.8 | 1999.5 | 0.01 | 7 | 900 | 7/0 | 0.033 | 2000.0 | yes |
| 369/92 | 60 | 4001 | 37.6 | 1.0 | 1.0 | 2000 | 2034.5 (1.4) | 184.8/250.2/37.6/3.0/1.7 | 2000.0 | 0.01 | 4 | 300 | 3/1 | 0.033 | 2000.0 | yes |
| 369/100 | 60 | 4001 | 1.1 | 5.1 | 1.0 | 8000 | 8138 (5.1) | 4.9/19.6/15.2/5.1/2.1 | 7998.7 | 0.95 | 3 | 3780 | 17/0 | 0.040 | 8000.0 | yes |
| 376/108 | 60 | 16001 | 1.5 | 53.7 | 1.1 | 8000 | 2000 (1.5) | 56.1/53.7/74.9/18.3/4.6 | 7998.1 | 0.04 | 10 | 3180 | 18/0 | 0.256 | 8000.0 | yes |
| 384/46 | 60 | 16001 | 2.0 | 554.0 | 1.2 | 8000 | 24414 (3.0) | 4319.7/137.7/2511.9/554.0/9.7 | 8002.8 | 0.01 | 18 | 3540 | 29/2 | 0.255 | 8000.0 | yes |
| 384/47 | 60 | 16001 | 1.2 | 13.3 | 1.2 | 8000 | 24414 (1.6) | 3319.7/6.5/68.1/13.3/1.1 | 8005.4 | 0.08 | 4 | 420 | 4/0 | 0.251 | 8000.0 | yes |
| 384/48 | 60 | 16001 | 1.1 | 7.9 | 1.0 | 8000 | 24414 (1.6) | 3359.9/4.9/46.3/7.9/1.2 | 8003.5 | 0.05 | 3 | 420 | 3/0 | 0.252 | 8000.0 | yes |
| 384/49 | 60 | 16001 | 1.3 | 22.7 | 1.4 | 8000 | 4000 (1.6) | 4478.6/12.8/138.2/22.7/1.4 | 8004.5 | 0.01 | 6 | 1860 | 6/0 | 0.254 | 8000.0 | yes |
| 399/132 | 25 | 16001 | 1.3 | 15.5 | 1.2 | 8000 | 8138 (1.5) | 262.9/14.8/32.3/15.5/1.4 | 8000.1 | 0.08 | 4 | 420 | 4/0 | 0.254 | 8000.0 | yes |
| 399/133 | 25 | 16001 | 1.2 | 23.2 | 1.3 | 8000 | 8138 (1.7) | 304.7/23.2/53.9/19.4/1.3 | 8001.5 | 0.02 | 4 | 420 | 4/0 | 0.255 | 8000.0 | yes |
| 400/72 | 60 | 16001 | 1.5 | 1.6 | 475.5 | 16000 | 16276 (258.5) | 624.0/258.5/508.5/475.5/17.2 | 15999.1 | 0.11 | 16 | 6660 | 52/1 | 0.256 | 16000.0 | yes |
| 400/73 | 60 | 16001 | 2.2 | 1.3 | 737.5 | 16000 | 16276 (715.7) | 715.7/737.5/1404.1/768.6/17.8 | 16000.1 | 0.07 | 17 | 6660 | 51/2 | 0.256 | 16000.0 | yes |
| 404/39 | 60 | 16001 | 1.6 | 415.6 | 1.1 | 8000 | 2000 (1.6) | 415.6/4189.0/2370.5/319.6/78.2 | 8002.2 | 0.02 | 17 | 3900 | 32/1 | 0.266 | 8000.0 | yes |
| 404/40 | 26 | 16001 | 1.9 | 330.4 | 1.3 | 8000 | 8138 (2.0) | 330.4/1336.8/948.8/217.6/69.0 | 8000.0 | 0.04 | 17 | 3900 | 31/2 | 0.264 | 8000.0 | yes |
| 405/102 | 60 | 16001 | 1.4 | 358.8 | 1.1 | 8000 | 8138 (1.5) | 678.9/135.8/546.5/358.8/5.9 | 8003.1 | 0.02 | 16 | 3900 | 32/1 | 0.255 | 8000.0 | yes |
| 405/103 | 60 | 16001 | 1.7 | 817.8 | 1.2 | 8000 | 2000 (1.7) | 933.4/374.3/1300.5/817.8/12.3 | 8002.6 | 0.07 | 17 | 3900 | 32/2 | 0.254 | 8000.0 | yes |
| 405/104 | 60 | 16001 | 2.0 | 1023.7 | 1.2 | 8000 | 2000 (2.0) | 1094.3/402.5/1622.8/1023.7/15.6 | 8003.6 | 0.02 | 17 | 3900 | 32/4 | 0.254 | 8000.0 | yes |
| 405/105 | 60 | 16001 | 2.0 | 894.9 | 1.2 | 8000 | 2000 (2.0) | 1274.6/511.7/1585.9/894.9/13.3 | 8002.3 | 0.02 | 17 | 3900 | 32/2 | 0.254 | 8000.0 | yes |
| 405/106 | 60 | 16001 | 2.0 | 1016.0 | 1.2 | 8000 | 2000 (2.0) | 1541.2/734.0/1927.3/1016.0/15.5 | 8003.3 | 0.03 | 18 | 3900 | 32/5 | 0.254 | 8000.0 | yes |
| 418/77 | 60 | 16001 | 1.2 | 5.2 | 1.2 | 8000 | 8138 (1.4) | 33.3/20.6/5.2/2.3/1.1 | 8000.8 | 0.09 | 3 | 300 | 3/0 | 0.255 | 8000.0 | yes |
| 466/128 | 60 | 16001 | 2.4 | 450.7 | 1.1 | 8000 | 4000 (3.5) | 3814.5/273.3/670.6/450.7/6.2 | 8004.5 | 0.03 | 16 | 3180 | 20/6 | 0.255 | 8000.0 | yes |
| 466/129 | 60 | 16001 | 2.4 | 264.3 | 1.1 | 8000 | 4000 (3.4) | 3346.3/186.3/429.3/264.3/4.2 | 8004.1 | 0.02 | 13 | 3420 | 19/5 | 0.255 | 8000.0 | yes |
| 466/132 | 62 | 16001 | 2.3 | 258.2 | 1.1 | 8000 | 4000 (2.3) | 3126.2/167.4/396.8/258.2/3.0 | 8001.1 | 0.04 | 11 | 3000 | 15/4 | 0.254 | 8000.0 | yes |
| 466/133 | 60 | 16001 | 5.6 | 1069.1 | 1.1 | 8000 | 2000 (5.6) | 2849.7/233.5/1213.0/1069.1/11.6 | 8003.1 | 0.02 | 26 | 3420 | 28/19 | 0.254 | 8000.0 | yes |
| 466/134 | 60 | 16001 | 5.1 | 1085.4 | 1.0 | 8000 | 2000 (5.1) | 2930.9/407.9/1362.7/1085.4/10.0 | 8003.3 | 0.01 | 26 | 3420 | 27/17 | 0.253 | 8000.0 | yes |
| 466/135 | 60 | 16001 | 4.9 | 960.7 | 1.1 | 8000 | 2000 (4.9) | 2703.9/276.1/989.0/960.7/9.0 | 8001.6 | 0.04 | 25 | 3180 | 24/15 | 0.254 | 8000.0 | yes |
| 511/89 | 60 | 16001 | 1.2 | 11.3 | 1.2 | 8000 | 24000 (1.4) | 205.6/51.0/11.3/4.3/1.5 | 7999.1 | 0.05 | 4 | 3780 | 15/0 | 0.254 | 8000.0 | yes |
| 511/90 | 60 | 16001 | 1.3 | 14.0 | 1.0 | 8000 | 4000 (1.4) | 177.2/59.2/14.0/5.3/2.3 | 7999.4 | 0.04 | 6 | 3780 | 18/0 | 0.254 | 8000.0 | yes |
| 511/91 | 60 | 16001 | 1.5 | 93.5 | 1.1 | 8000 | 4000 (1.7) | 590.1/241.6/93.5/28.3/6.4 | 7998.2 | 0.01 | 10 | 3780 | 22/2 | 0.253 | 8000.0 | yes |
| 511/92 | 60 | 16001 | 1.6 | 63.1 | 1.1 | 8000 | 2000 (1.6) | 496.0/168.7/63.1/22.6/6.6 | 7999.7 | 0.04 | 9 | 3780 | 22/2 | 0.254 | 8000.0 | yes |
| 511/93 | 60 | 16001 | 1.9 | 57.0 | 1.2 | 8000 | 2000 (1.9) | 236.2/151.8/57.0/23.0/8.4 | 7997.3 | 0.02 | 12 | 3780 | 24/2 | 0.254 | 8000.0 | yes |
| 511/94 | 60 | 16001 | 1.8 | 39.9 | 1.1 | 8000 | 4000 (1.8) | 394.0/94.7/39.9/16.8/7.2 | 7999.8 | 0.03 | 12 | 3780 | 24/2 | 0.253 | 8000.0 | yes |
| 511/95 | 60 | 16001 | 1.4 | 33.7 | 1.0 | 8000 | 2000 (1.4) | 152.9/103.4/33.7/11.0/4.9 | 8000.9 | 0.02 | 8 | 3780 | 19/1 | 0.254 | 8000.0 | yes |
| 511/96 | 60 | 16001 | 1.4 | 56.9 | 1.1 | 8000 | 4000 (1.7) | 331.8/149.9/56.9/17.7/6.2 | 7997.8 | 0.01 | 9 | 3780 | 20/2 | 0.253 | 8000.0 | yes |
| 511/97 | 60 | 16001 | 1.2 | 19.4 | 1.0 | 8000 | 4000 (1.3) | 207.8/75.3/19.4/6.0/2.3 | 8000.8 | 0.06 | 6 | 3300 | 15/0 | 0.254 | 8000.0 | yes |
| 511/117 | 60 | 16001 | 1.5 | 42.0 | 1.1 | 8000 | 8138 (1.7) | 365.0/67.4/42.0/30.0/2.0 | 7998.6 | 0.10 | 9 | 3780 | 21/2 | 0.255 | 8000.0 | yes |
| 511/118 | 60 | 16001 | 2.8 | 226.4 | 1.1 | 8000 | 2000 (2.8) | 613.8/368.2/226.4/129.2/4.7 | 7997.7 | 0.03 | 12 | 3900 | 25/12 | 0.256 | 8000.0 | yes |
| 511/123 | 60 | 16001 | 1.4 | 81.1 | 1.1 | 8000 | 8138 (1.4) | 1014.0/124.8/81.1/40.9/2.6 | 7996.1 | 0.02 | 9 | 3900 | 22/5 | 0.255 | 8000.0 | yes |
| 511/124 | 60 | 16001 | 1.6 | 78.3 | 1.2 | 8000 | 2000 (1.6) | 230.2/107.4/78.3/57.9/4.0 | 7997.6 | 0.01 | 10 | 3900 | 24/7 | 0.255 | 8000.0 | yes |
| 511/125 | 60 | 16001 | 1.7 | 112.1 | 1.0 | 8000 | 2000 (1.7) | 586.7/200.1/112.1/67.0/3.4 | 7998.8 | 0.01 | 10 | 2580 | 12/0 | 0.254 | 8000.0 | yes |
| 511/127 | 60 | 16001 | 1.7 | 42.4 | 1.3 | 8000 | 2000 (1.7) | 117.5/69.0/42.4/41.1/4.1 | 8000.0 | 0.02 | 12 | 3900 | 28/4 | 0.253 | 8000.0 | yes |
| 515/6 | 30 | 32001 | 1.6 | 2.3 | 180.6 | 16000 | 8000 (2.3) | 180.6/401.1/173.9/207.3/50.6 | 15998.6 | 0.09 | 17 | 2580 | 20/3 | 0.161 | 16000.0 | yes |
| 515/7 | 30 | 32001 | 1.4 | 1.7 | 137.7 | 16000 | 4000 (1.8) | 156.0/288.7/110.4/137.7/41.2 | 15999.4 | 0.17 | 15 | 3000 | 17/4 | 0.160 | 16000.0 | yes |
| 515/8 | 30 | 32001 | 1.3 | 1.8 | 130.0 | 16000 | 8000 (1.8) | 137.4/248.4/110.8/130.0/35.1 | 15997.9 | 0.09 | 14 | 2580 | 16/2 | 0.160 | 16000.0 | yes |
| 515/13 | 30 | 32001 | 1.6 | 2.2 | 92.9 | 16000 | 8000 (2.2) | 108.0/136.6/69.2/92.9/37.1 | 16001.1 | 0.16 | 19 | 3000 | 20/5 | 0.160 | 16000.0 | yes |
| 515/14 | 30 | 32001 | 1.5 | 2.1 | 117.1 | 16000 | 8000 (2.1) | 117.1/231.4/99.8/119.5/38.7 | 16000.0 | 0.04 | 16 | 3000 | 17/4 | 0.156 | 16000.0 | yes |

Stimulus artefact, lock, NaN and padding; `eeg = annex key` is the identity check above:

| run | best rate (Hz) | artefact channels | artefact drop 0.16->0.24 (dB) | epochs with artefact at centre | epochs with sharpest jump at centre | centre ratio median | channels | channels per epoch min/median/max | NaN trial x channel | epochs with <= 5 channels | last sample = 0 | second-to-last = 0 | eeg = annex key |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 369/91 | 2000 | 240 | -0.6 | 60/60 | 60/60 | 97.1 | 256 | 98/245/255 | 0.071 | - | 14270/14270 | 4/14270 | yes |
| 369/92 | 2000 | 210 | 0.3 | 60/60 | 60/60 | 106.3 | 256 | 141/243/256 | 0.076 | - | 14186/14186 | 3/14186 | yes |
| 369/100 | 8000 | 3 | -2.7 | 0/60 | 1/60 | 2.8 | 202 | 2/32/102 | 0.828 | 9,13,17,21,25,29,33,37,41,45,49,53,57 | 2082/2082 | 0/2082 | yes |
| 376/108 | 8000 | 1 | -8.0 | 60/60 | 60/60 | 1042.6 | 256 | 246/256/256 | 0.004 | - | 15306/15306 | 2/15306 | yes |
| 384/46 | 8000 | 6 | -2.3 | 60/60 | 60/60 | 661.3 | 255 | 106/205/245 | 0.208 | - | 12114/12114 | 1/12114 | yes |
| 384/47 | 8000 | 250 | -3.5 | 60/60 | 60/60 | 647.0 | 256 | 120/217.5/238 | 0.176 | - | 12659/12659 | 1/12659 | yes |
| 384/48 | 8000 | 252 | -4.1 | 60/60 | 60/60 | 788.0 | 256 | 163/215/244 | 0.179 | - | 12609/12609 | 3/12609 | yes |
| 384/49 | 8000 | 252 | -1.8 | 60/60 | 60/60 | 713.7 | 256 | 144/217/243 | 0.164 | - | 12842/12842 | 1/12842 | yes |
| 399/132 | 8000 | 249 | -14.6 | 25/25 | 25/25 | 910.2 | 255 | 117/212/250 | 0.207 | - | 5053/5053 | 0/5053 | yes |
| 399/133 | 8000 | 246 | -14.4 | 25/25 | 25/25 | 897.7 | 255 | 109/210/250 | 0.226 | - | 4935/4935 | 0/4935 | yes |
| 400/72 | 16000 | 7 | 13.8 | 60/60 | 60/60 | 623.8 | 256 | 96/213/244 | 0.199 | - | 12304/12304 | 2/12304 | yes |
| 400/73 | 16000 | 7 | 13.9 | 60/60 | 60/60 | 597.6 | 256 | 83/218/249 | 0.179 | - | 12605/12605 | 5/12605 | yes |
| 404/39 | 8000 | 2 | -12.5 | 60/60 | 60/60 | 728.4 | 256 | 104/215.5/248 | 0.178 | - | 12621/12621 | 4/12621 | yes |
| 404/40 | 8000 | 2 | -4.6 | 26/26 | 26/26 | 736.6 | 256 | 125/216/244 | 0.184 | - | 5429/5429 | 0/5429 | yes |
| 405/102 | 8000 | 8 | -10.5 | 60/60 | 60/60 | 843.0 | 256 | 99/223.5/250 | 0.179 | - | 12618/12618 | 7/12618 | yes |
| 405/103 | 8000 | 8 | -9.6 | 60/60 | 60/60 | 862.2 | 255 | 52/234/253 | 0.131 | - | 13292/13292 | 7/13292 | yes |
| 405/104 | 8000 | 8 | -8.3 | 60/60 | 60/60 | 862.6 | 254 | 126/227/252 | 0.124 | - | 13351/13351 | 2/13351 | yes |
| 405/105 | 8000 | 8 | -6.1 | 60/60 | 60/60 | 808.3 | 255 | 152/222.5/249 | 0.165 | - | 12775/12775 | 4/12775 | yes |
| 405/106 | 8000 | 8 | -9.3 | 60/60 | 60/60 | 853.6 | 256 | 158/232/249 | 0.115 | - | 13598/13598 | 6/13598 | yes |
| 418/77 | 8000 | 57 | -1.6 | 60/60 | 60/60 | 774.9 | 191 | 86/145.5/184 | 0.259 | - | 8490/8490 | 5/8490 | yes |
| 466/128 | 8000 | 110 | 0.1 | 60/60 | 60/60 | 194.9 | 255 | 45/232.5/254 | 0.207 | - | 12133/12133 | 0/12133 | yes |
| 466/129 | 8000 | 0 | n/a | 60/60 | 60/60 | 729.7 | 255 | 40/241/255 | 0.158 | - | 12882/12882 | 1/12882 | yes |
| 466/132 | 8000 | 152 | 3.1 | 61/62 | 59/62 | 131.2 | 256 | 58/244.5/256 | 0.137 | - | 13697/13697 | 1/13697 | yes |
| 466/133 | 8000 | 135 | -1.2 | 60/60 | 59/60 | 197.6 | 256 | 50/243.5/255 | 0.145 | - | 13128/13128 | 1/13128 | yes |
| 466/134 | 8000 | 126 | -1.7 | 60/60 | 60/60 | 199.7 | 256 | 32/244.5/256 | 0.121 | - | 13496/13496 | 1/13496 | yes |
| 466/135 | 8000 | 51 | -4.1 | 60/60 | 60/60 | 277.6 | 256 | 68/246/255 | 0.104 | - | 13767/13767 | 1/13767 | yes |
| 511/89 | 8000 | 103 | 1.3 | 60/60 | 59/60 | 326.5 | 192 | 65/171/191 | 0.151 | - | 9783/9783 | 1/9783 | yes |
| 511/90 | 8000 | 98 | 1.2 | 60/60 | 60/60 | 330.1 | 192 | 66/171.5/190 | 0.143 | - | 9872/9872 | 2/9872 | yes |
| 511/91 | 8000 | 87 | 1.3 | 60/60 | 60/60 | 316.8 | 192 | 105/172/188 | 0.141 | - | 9893/9893 | 0/9893 | yes |
| 511/92 | 8000 | 90 | 1.3 | 60/60 | 60/60 | 353.8 | 192 | 109/168/187 | 0.145 | - | 9847/9847 | 0/9847 | yes |
| 511/93 | 8000 | 86 | 1.3 | 60/60 | 60/60 | 311.8 | 192 | 84/171.5/189 | 0.147 | - | 9831/9831 | 0/9831 | yes |
| 511/94 | 8000 | 83 | 1.4 | 60/60 | 60/60 | 305.0 | 192 | 120/172.5/189 | 0.114 | - | 10201/10201 | 1/10201 | yes |
| 511/95 | 8000 | 95 | 0.9 | 60/60 | 60/60 | 315.0 | 192 | 80/169/187 | 0.148 | - | 9820/9820 | 0/9820 | yes |
| 511/96 | 8000 | 75 | 1.4 | 60/60 | 59/60 | 341.5 | 192 | 90/169/189 | 0.140 | - | 9904/9904 | 2/9904 | yes |
| 511/97 | 8000 | 89 | 1.2 | 60/60 | 60/60 | 294.3 | 192 | 90/165.5/189 | 0.151 | - | 9776/9776 | 2/9776 | yes |
| 511/117 | 8000 | 95 | 0.8 | 60/60 | 60/60 | 181.0 | 192 | 99/168.5/189 | 0.148 | - | 9816/9816 | 0/9816 | yes |
| 511/118 | 8000 | 105 | 0.8 | 60/60 | 60/60 | 221.5 | 192 | 116/176.5/189 | 0.111 | - | 10244/10244 | 3/10244 | yes |
| 511/123 | 8000 | 93 | 1.1 | 60/60 | 60/60 | 255.1 | 192 | 86/173/190 | 0.145 | - | 9849/9849 | 0/9849 | yes |
| 511/124 | 8000 | 93 | 1.3 | 60/60 | 60/60 | 385.3 | 192 | 54/167.5/191 | 0.147 | - | 9822/9822 | 1/9822 | yes |
| 511/125 | 8000 | 89 | 0.9 | 60/60 | 60/60 | 306.4 | 191 | 83/170.5/189 | 0.136 | - | 9906/9906 | 0/9906 | yes |
| 511/127 | 8000 | 84 | 1.3 | 60/60 | 60/60 | 295.7 | 192 | 66/176/192 | 0.132 | - | 9998/9998 | 1/9998 | yes |
| 515/6 | 16000 | 3 | 26.4 | 30/30 | 30/30 | 2974.2 | 255 | 155/245/252 | 0.075 | - | 7074/7074 | 15/7074 | yes |
| 515/7 | 16000 | 173 | 37.4 | 30/30 | 30/30 | 864.3 | 255 | 181/235.5/252 | 0.106 | - | 6836/6836 | 9/6836 | yes |
| 515/8 | 16000 | 3 | 26.2 | 30/30 | 30/30 | 2615.8 | 255 | 137/229.5/252 | 0.110 | - | 6808/6808 | 4/6808 | yes |
| 515/13 | 16000 | 152 | 24.4 | 30/30 | 30/30 | 732.2 | 255 | 83/236.5/251 | 0.134 | - | 6622/6622 | 8/6622 | yes |
| 515/14 | 16000 | 146 | 36.1 | 30/30 | 30/30 | 747.8 | 255 | 152/236/250 | 0.107 | - | 6831/6831 | 7/6831 | yes |

By measured rate:

| best rate (Hz) | runs | BIDS rate = measured | fit min (Hz) | fit max (Hz) | drop min (dB) | drop max (dB) | roll-off min | roll-off max |
|---|---|---|---|---|---|---|---|---|
| 2000 | 2 | 2 | 1999.5 | 2000.0 | -0.6 | 0.3 | 0.033 | 0.033 |
| 8000 | 37 | 37 | 7996.1 | 8005.4 | -14.6 | 3.1 | 0.040 | 0.266 |
| 16000 | 7 | 7 | 15997.9 | 16001.1 | 13.8 | 37.4 | 0.156 | 0.256 |

Values quoted in the README (1.0.3):
- Rates: 37 runs at 8000 Hz (sub-369 run 100 included: fit 7998.7 +/- 0.9 Hz, odd 60 Hz harmonics only, up to 3780 Hz),
  2 at 2000 Hz (sub-369 runs 91/92), 7 at 16000 Hz (sub-400, sub-515); `SamplingFrequency` equals the measured rate in
  46/46 runs. Fits: 1999.5-2000.0, 7996.1-8005.4, 15997.9-16001.1 Hz.
- Artefact spectrum, drop from 0.16 to 0.24 cycle/sample: sub-400 13.8 and 13.9 dB, sub-515 24.4-37.4 dB, 8 kHz runs
  -14.6 to 3.1 dB (negative: rises), 2 kHz runs -0.6 and 0.3 dB.
- Roll-off: sub-400 0.256 cycle/sample; the 8 kHz runs with 16001-sample epochs 0.251-0.266.
- sub-369 run 100: 0/60 epochs with an artefact at the centre (every other run: 61/62 or all epochs); NaN in 0.828 of its
  trial x channel pairs (other runs 0.004-0.259); epochs 9, 13, ..., 57 keep <= 5 channels (minimum 2).
- Last sample = 0 in every finite value of every run (control, second-to-last sample: 0-15 zeros per run).

## Coverage
46 of 46 runs (all `EPdata3D.mat` of the release, all runs in BIDS) for the mains comb and fit, lock, NaN, padding,
identity and BIDS fields; artefact spectrum 45 of 46 (466/129: no channel passes the selection, `n/a`).

## sha256 of the release files
```
36a2f196efedbdc9a1fcf9e1c1829d071da5d9011739804822d52cbad8694fa3  369/91/EPdata3D.mat
96fb06d83b6d56b483d9a4dc681226f8f615409ff579adf15b8ad5dd80d82efc  369/92/EPdata3D.mat
eaf17956a38a93a75bcb06c29be56582127b18ce040665267179ef79cdf7f68c  369/100/EPdata3D.mat
f614541bca52586606e392c2e02b1b823cd4f2c14ae6a57deeed86bd2a4735eb  376/108/EPdata3D.mat
79e0e7f83d8882c8f73829e19a94eef3d24191cee4e239d4da7aafa2b5ad8a5b  384/46/EPdata3D.mat
290c19d1c717f8da557fc15c334c92804338fdfde702031cf7677df32a23ce2f  384/47/EPdata3D.mat
41a500e3b0ac477686b07b142c27457031450c92945cfe888fab34344369b144  384/48/EPdata3D.mat
ecae86096ac42d01d727b0136dd1d64f2a5cda0d9d58ab5a4c73859893b2a2e1  384/49/EPdata3D.mat
284cbde4cdddcc3eb6cab82cc8c77b30fd7868497ede454d5b246b3698508340  399/132/EPdata3D.mat
3618b63977de18f8228d2e5f209f47e97a5de89d45a92a54d7272037424f2288  399/133/EPdata3D.mat
c0f98aa5ab08eb0f4be16c32a9ee668041404c042ed42414190ff405aac4f4e1  400/72/EPdata3D.mat
12080148465696633d9478b866094685f57d9ec01eef5d1c2b525fef705f57b6  400/73/EPdata3D.mat
89e365634946ef80e269ca8073e82329d37336c06ed82171a4ecd0bd8f65ad36  404/39/EPdata3D.mat
fca8e1820d5d17ee100a115c50f4bf86a419f73fc7089d32066d6122a026b361  404/40/EPdata3D.mat
631cb2a918fe30bf66df6e1dcd6c4fe1a8b0ad455f33401aa5d5c1f1073554b1  405/102/EPdata3D.mat
389bd56c2c0d7e2b980616e4c91320b08e9fb3b18877adc178d44d22a65b391a  405/103/EPdata3D.mat
1a85d6e05766a84632aef12905c0a92d2b7d60f0556a6d380dbe8319cbdd4ee2  405/104/EPdata3D.mat
cef751e5636b36b7544199fc1dd47549c25e3c3f212af895c4623fbc973bc07c  405/105/EPdata3D.mat
16bb1948fa54d6ae7ce3bc7176e48589e7f31422359381765c51228d34bfbecd  405/106/EPdata3D.mat
6f9b2812c7336e115462dc4fdfb7b399ba2cf021e966f6a5c2c6c98109be451a  418/77/EPdata3D.mat
bcb88f755234fc3716c6ba408a188df58b8fa88a5a75aa3a133c97ef7d80c341  466/128/EPdata3D.mat
d93b2d23b6d3543b59344afbfe8409524eead377b84868aec7cfeb0bd0f9d994  466/129/EPdata3D.mat
74b58d5db28c22d6f11f636635becd6584f003d1a9962c77845d0a8e1ed217ed  466/132/EPdata3D.mat
543cb3232222adbd7630672b58674017c151010bc192ea1ec0308a1eff61231b  466/133/EPdata3D.mat
28e4624f1f5ff0fc4d01fbc0311390eb8593cd37172a2a905a105e3ebdcb449b  466/134/EPdata3D.mat
20e75b05b933f58b7443e3decc4df248fb0e4212cd44d2840a9f542363f8bc7b  466/135/EPdata3D.mat
aefd7f66a04a138d574e2245d23e6fa776e617ad121016ba8e7f8e3795b305af  511/89/EPdata3D.mat
111b2b93c0f801c86e7ec56f91ec19947e396b8772fbd4733ef554cf68737b45  511/90/EPdata3D.mat
f8e7169e7fcc93f40b4008629f0050c246503ee79619cd4663d875f80a9ea31a  511/91/EPdata3D.mat
28a7378b75b47d35f094f6d215e59c19fa4ac66d696b7a66a728564752140d39  511/92/EPdata3D.mat
7d846c0b48195762a0db8978356b5bc3b9ec0e2ca19a7afc7a391525e911c515  511/93/EPdata3D.mat
de97552b89a4f2a4560cb463a63748975fa72611e5596194f9e2b4b51f8a6404  511/94/EPdata3D.mat
6f81d65b57142f4cb233a60b2c317aedfa5193955cf659f1c15d0fc5fdcb91f8  511/95/EPdata3D.mat
17eb5d1f8148a0d9dd82b4ae6bcde70a3ee51996c75b253ffb0b5aab7ae70b44  511/96/EPdata3D.mat
12435b302f3a9b6d46e48cb689b7c015c926bc48bd6b0d1b1f1881f56d7e0c86  511/97/EPdata3D.mat
68003a75fb62e4e5b654f9d48e9e3d7e57439e062a3bc4cdce27f68075b0a678  511/117/EPdata3D.mat
c20d2df88accbc266e37862263dc66b1af556ba5327d63165422f5c8a1ce7489  511/118/EPdata3D.mat
4358554dbcf47b195ec4c3ab58210b5196404a54054335877bb239a36309aaea  511/123/EPdata3D.mat
bb57721e961d71a82eb1dd60592607c5513227dc96248dca89fb15d159aa03a6  511/124/EPdata3D.mat
3f6bd33fdf8944069b497ca7a50a3d0cf68cfa81ef2579aafe5edf24a4f0e98d  511/125/EPdata3D.mat
f902066daee8bfd740c88b64b9dda19714de36789609347d2a46c942ab9bf754  511/127/EPdata3D.mat
d20ed2069d7869b1e0a1bc1616336398b962f9ae013460ff3b71623655b66c42  515/6/EPdata3D.mat
06ea8bced9c05d90f4015d2c4cefad05e61eedb730704512b4435a26803f5a69  515/7/EPdata3D.mat
b84b0692802873f44fb2bbd087a368fa1ac19f545513b9dc326f8ae224b70d26  515/8/EPdata3D.mat
efd069e9324560b5307c227d4e63651b86a82aab024ce08999958e2d64c9b4c7  515/13/EPdata3D.mat
17cf45ee7702a45687ff9a16ae27bdcb61c77a04eef241ec225ed5ea82d62a52  515/14/EPdata3D.mat
```
