import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
ARCHIVE_TITLE = "CMSC Software History"
FONT_ASSETS = {
    "Audiowide.woff2": "https://fonts.gstatic.com/s/audiowide/v22/l7gdbjpo0cum0ckerWCdlg_OMRlABg.woff2",
    "Audiowide-OFL.txt": "https://raw.githubusercontent.com/google/fonts/main/ofl/audiowide/OFL.txt",
}


def visible_entries(path):
    if path.is_dir():
        yield from sorted(entry for entry in path.iterdir() if not entry.name.startswith("."))


def sections(path):
    for entry in visible_entries(path):
        if entry.is_dir():
            if not re.fullmatch(r"[a-z0-9-]+", entry.name):
                raise ValueError(f"Invalid directory slug: {entry}")
            yield entry


def images(path):
    return (entry for entry in visible_entries(path) if entry.suffix == ".png" and entry.is_file())


def read_title(path, fallback=None):
    if path.is_file() and path.stat().st_size:
        with path.open(encoding="utf-8") as file:
            return file.readline().rstrip("\n")
    if fallback is not None:
        return fallback
    raise ValueError(f"Missing title: {path}")


def fragment(path):
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def station_cover(station):
    override = station / "tile.png"
    return override if override.is_file() else next(images(station), None)


def ship_cover(ship, stations):
    override = ship / "tile.png"
    if override.is_file():
        return override
    for station in stations:
        cover = station_cover(station)
        if cover is not None:
            return cover
    return None


def thumbnail_command():
    if shutil.which("magick"):
        return ["magick", "{source}", "-thumbnail", "640x480>", "-strip", "{dest}"]
    if shutil.which("sips"):
        return ["sips", "-Z", "640", "{source}", "--out", "{dest}"]
    raise ValueError("Install ImageMagick (magick), or use macOS sips.")


def copy_assets(stage):
    for filename, url in FONT_ASSETS.items():
        asset = ASSETS / filename
        if not asset.is_file() or not asset.stat().st_size:
            download = stage / filename
            subprocess.run(["curl", "-fsSL", url, "-o", str(download)], check=True)
            download.replace(asset)
    dest = stage / "assets"
    dest.mkdir()
    for asset in visible_entries(ASSETS):
        shutil.copyfile(asset, dest / asset.name)


def generate(stage):
    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.globals["archive_title"] = ARCHIVE_TITLE
    thumb = thumbnail_command()
    copy_assets(stage)

    def render(template, dest, page_title, root, breadcrumbs=(), **context):
        html = env.get_template(template).render(
            page_title=page_title, root=root, breadcrumbs=breadcrumbs, **context
        )
        dest.write_text(html, encoding="utf-8")

    def make_tile(source, parent, title, cover):
        dest = parent / source.name
        dest.mkdir()
        if cover is not None:
            command = [arg.format(source=cover, dest=dest / "tile.png") for arg in thumb]
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
        return {"slug": source.name, "title": title, "has_image": cover is not None}

    ship_tiles = []
    for ship in sections(CONTENT / "ships"):
        if ship.name == "assets":
            raise ValueError("Ship slug assets is reserved.")
        ship_title = read_title(ship / "title.txt")
        stations = list(sections(ship / "stations"))
        ship_dest = stage / ship.name
        ship_tiles.append(make_tile(ship, stage, ship_title, ship_cover(ship, stations)))
        station_tiles = []
        for station in stations:
            station_title = read_title(station / "title.txt")
            station_dest = ship_dest / station.name
            station_tiles.append(make_tile(station, ship_dest, station_title, station_cover(station)))
            for image in images(station):
                if image.name != "tile.png":
                    shutil.copyfile(image, station_dest / image.name)
            render(
                "fragment.html", station_dest / "index.html", f"{station_title} — {ship_title}", "../../",
                [(ship_title, "../index.html"), (station_title, None)],
                body=(station / "body.html").read_text(encoding="utf-8"),
            )
        render(
            "ship.html", ship_dest / "index.html", f"{ship_title} — {ARCHIVE_TITLE}", "../",
            [(ship_title, None)], title=ship_title, tiles=station_tiles,
            about=fragment(ship / "about.html"), references=fragment(ship / "references.html"),
        )

    render(
        "home.html", stage / "index.html", ARCHIVE_TITLE, "./",
        about=fragment(CONTENT / "ships" / "about.html"), tiles=ship_tiles,
    )
    for page in visible_entries(CONTENT):
        if page.suffix != ".html" or not page.is_file():
            continue
        if page.name == "index.html":
            raise ValueError("content/index.html is reserved. Edit content/ships/about.html instead.")
        title = read_title(page.with_suffix(".title.txt"), re.sub(r"[_-]", " ", page.stem))
        render("fragment.html", stage / page.name, f"{title} — {ARCHIVE_TITLE}", "./", body=fragment(page))
    (stage / ".nojekyll").touch()


def main():
    # Leave the published site in place if any generation step fails.
    output = ROOT / "docs"
    with TemporaryDirectory(prefix="site-build.", dir=ROOT) as work:
        stage = Path(work) / "docs"
        stage.mkdir()
        generate(stage)
        if output.exists():
            shutil.rmtree(output)
        stage.rename(output)
    print(f"Open {output / 'index.html'}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Build failed: {error}") from error
