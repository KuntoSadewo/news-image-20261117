# The Bridge Falls — news-image-20261117

[![make.fun](https://make.fun/badge/news-image-20261117.svg)](https://make.fun/c/news-image-20261117)
[![rank](https://make.fun/badge/news-image-20261117/KuntoSadewo/news-image-20261117/rank.svg)](https://make.fun/c/news-image-20261117)
[![reward](https://make.fun/badge/news-image-20261117/KuntoSadewo/news-image-20261117/reward.svg)](https://make.fun/c/news-image-20261117)

Entry for the [make.fun bounty "Sum up 17 November's world news in one image"](https://make.fun/c/news-image-20261117) — a program that draws one newspaper front page summing up Tuesday 17 November 2026.

## The image

**"THE WORLD — KERCH BRIDGE FALLS."** The day's dominant story, as reported on 17 November 2026 (Reuters, CNN, Le Monde): Ukraine struck the Kerch Bridge linking Russia to occupied Crimea for a second straight day and its road arch collapsed into the strait, while Russia answered by hitting two bridges over the Dnipro in Kyiv. The front page also carries the day's two other big stories — U.S. strikes on an Iranian missile site on Qeshm Island and Iranian drone fire at a U.S. radar base in Bahrain, with a fourth tanker burning east of the Strait of Hormuz — and Donald Trump leaving for Asia ahead of Thursday's first-ever Xi–Trump–Putin meeting in Shenzhen. Brent crude near $93 in the footer.

## How it runs

`main.py` (Python 3.13, standard library only, no network) draws the whole front page in code — a small scanline rasteriser and a hand-made 5×7 bitmap font — and writes it to `/output/entry.png` (1024×1024 PNG, deterministic: two runs write identical bytes).

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```
