# Image Converter

A small Tkinter desktop app that batch-converts images to JPG, with optional resizing and drag-and-drop folder selection.

## Features

- **PNG → JPG** and **JPG → JPG** batch conversion (toggle the input formats independently)
- **Adjustable JPG quality** (1–100)
- **Optional resize**, with two modes:
  - **Max dimension** — fit within a max width and/or height; aspect ratio preserved; never upscales
  - **Percentage** — proportional scale from 10% to 200%
- **Drag-and-drop** a folder (or any file inside one) onto the Input or Output field — Browse buttons still work
- **Subfolder traversal** (preserves directory structure in the output)
- **Overwrite toggle** for existing JPGs; safe in-place re-encode when input and output point to the same JPG (atomic temp-file replace)
- **Transparency-safe** flattening (RGBA / LA / palette-with-transparency are composited onto white before JPEG save)
- **Threaded** conversion with a live progress bar — UI stays responsive
- **Remembers** the last-used input/output folders between runs

## Requirements

- Python 3.9+ (tested on 3.13)
- [Pillow](https://pypi.org/project/Pillow/)
- [tkinterdnd2](https://pypi.org/project/tkinterdnd2/) (drag-and-drop support)

Tkinter ships with the standard Python installer on Windows and macOS. On Linux you may need `sudo apt install python3-tk` (or your distro's equivalent).

## Install

```bash
git clone https://github.com/<your-user>/img_converter.git
cd img_converter
pip install -r requirements.txt
```

## Run

```bash
python img_converter.py
```

## Usage

1. **Pick an Input folder** — drag a folder onto the Input field, or click **Browse**.
2. **Pick an Output folder** the same way (it will be created if it doesn't exist).
3. Choose **input formats** (PNG, JPG/JPEG, or both) and toggle **Process subfolders** if needed.
4. Set the **JPG quality** slider.
5. Optional: enable **Resize images** and pick a mode:
   - *Max dimension* — leave width or height blank for "unlimited" on that axis.
   - *Percentage* — drag the slider; >100% upscales.
6. Click **Convert Images**. When done, **Open Output Folder** reveals the result.

### In-place JPG re-encoding

If you point Input and Output at the same folder while processing JPGs, each file would otherwise overwrite itself. The app handles this by writing to a temp file in the same folder and atomically replacing the original — so a crash mid-write won't leave a corrupted JPG. With **Overwrite existing JPGs** off, in-place writes are skipped instead.

## Files written by the app

- `converter_settings.json` — last-used Input/Output folders. Already listed in `.gitignore`.

## License

No license declared yet — add one (e.g. MIT) before publishing publicly if you want others to reuse the code.
