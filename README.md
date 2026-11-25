# CMSC Software History

From this folder, set up a Python virtual environment and build the site:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 build.py
```

On subsequent builds, activate the same environment and run `python3 build.py` again. The script renders Jinja templates and uses ImageMagick (`magick`) or macOS `sips` for tile thumbnails. Full-size screenshots are copied without changes.

Open `docs/index.html` directly. The generated site is self-contained: no Python, JavaScript, external web fonts, web server, or network access required to view it. Rebuilding replaces `docs/`; edit the sources instead. For GitHub Pages, commit `docs/` and select `/docs` as the publishing folder for your branch in Settings → Pages.

## Content layout

```text
templates/base.html
templates/home.html
templates/ship.html
templates/fragment.html
templates/tiles.html
content/<page>.html
content/<page>.title.txt
content/ships/about.html
content/ships/<ship>/title.txt
content/ships/<ship>/about.html
content/ships/<ship>/references.html
content/ships/<ship>/tile.png
content/ships/<ship>/stations/<station>/title.txt
content/ships/<ship>/stations/<station>/body.html
content/ships/<ship>/stations/<station>/tile.png
content/ships/<ship>/stations/<station>/<card>.png
```

Each `title.txt` contains a display title for navigation and the browser tab. The homepage intro is `content/ships/about.html`; each ship can also have its own `about.html` fragment above the screenshot tiles and an optional `references.html` fragment below them. Each station has a manually editable `body.html`: write the station heading, notes, and screenshot markup here, in the order you want them shown. Do not include a header, footer, or surrounding HTML document. Reference PNGs by filename, e.g. `<img src="master-display.png" alt="Master Display">`. The build copies screenshots alongside the page and does not generate or reorder the card markup. Use `id` on a card section if you want a direct link to it.

Optional `tile.png` files override the default cover selection. Galileo’s tile is the side-view drawing extracted from the Nav card’s `BMAP` 6573 in the original Navigation stack. Its previous login emblem (`PICT` 25233, embedded GIF) is preserved as `logo.png`. The other ship tiles use their Navigation stack login graphics: Maximus `PICT` 4752 and USN Galileo `PICT` 11073. Ship and station directories are listed in slug order; slugs use lowercase ASCII letters, digits, and hyphens.

The screenshots for USS Galileo, USS Maximus, and USN Galileo are stored in the content tree, so the archive can move independently of the emulator and original stacks. The generator never uploads or deploys anything.

Edit shared page markup in `templates/base.html`. Put standalone HTML fragments directly in `content/`, such as `content/hypercard.html`. The build inserts each fragment as HTML into the shared layout and keeps its filename. Titles and other template data are HTML-escaped automatically. An optional matching `.title.txt` sets the browser title; otherwise the build uses the filename. `index.html` is reserved for the generated ship index.

Headings use Audiowide. On the first build, `curl` downloads the font and license from Google Fonts into `assets/`. Those files are Git-ignored and reused on subsequent builds. The generated site includes both files and works offline.
