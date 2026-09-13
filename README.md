# CoinScope v0.1

An ad-free Linux workstation for capturing and organizing coin images from a USB microscope.

## U.S. cent catalog

The generated cent catalog covers 391 regular and proof date/mint records from
1850 through the final 2025 circulating issue. It includes broad grade-based
collector ranges, date-specific major varieties, and universal mint-error
inspection checks. The U.S. Mint ended circulating cent production in 2025, so
2026 is explicitly treated as not issued.

Catalog prices are conservative screening estimates, not offers or appraisals.
They help decide which coins deserve closer inspection or professional grading.
Regenerate and validate the catalog with:

```bash
python3 tools/build_cent_catalog.py
python3 tests/test_cent_catalog.py
```

## What works now

- Discovers Linux V4L2 cameras (`/dev/video*`) and displays their hardware names.
- Live microscope preview with coin-centering reticle.
- Captures separate obverse/front and reverse/back images at the camera's best available resolution.
- Reports a focus/sharpness score after each capture.
- Stores country, denomination, year, mint mark, and notes.
- Saves images and collection records locally in `data/` using SQLite.
- Responsive dark interface designed for a desktop monitor or touchscreen.

## Install and run on Thor

```bash
cd ~/CoinScope
chmod +x run-coinscope.sh
./run-coinscope.sh
```

The first launch creates a private Python environment and installs Flask and OpenCV. CoinScope opens at <http://127.0.0.1:5050>.

If Python cannot create the virtual environment:

```bash
sudo apt update
sudo apt install -y python3-opencv python3-venv v4l-utils
```

## Camera troubleshooting

Close Cheese, OBS, VLC, or any other program using the microscope, then run:

```bash
v4l2-ctl --list-devices
ls -l /dev/video*
```

If the browser shows a broken feed, switch to another entry with the same microscope name. Many UVC microscopes expose one capture device plus one metadata device.

## Data and privacy

CoinScope makes no external network calls while scanning. Images and records stay under `data/`; identification uses the local Gemma vision server and collector screening uses the bundled source-dated catalog.

CoinScope deliberately uses Ubuntu/JetPack's system OpenCV package rather than downloading a generic wheel. That is more reliable with USB cameras on both Thor and Jetson.

## Roadmap

1. Coin crop/background cleanup and rotation.
2. Local AI country, denomination, year, and mint-mark identification.
3. Known-variety inspection prompts and marked image regions.
4. Evidence-backed sold-price lookup with date, grade, and source.
5. Collection export, backup, and value dashboard.
