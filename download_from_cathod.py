import sys
import argparse
import pendulum
from pathlib import Path
import shutil
import json
import epycs.subprocess as es

ROOT = Path(__file__).resolve().parent


cathod = es.find_program("e3-cathod")


def current_platform():
    if sys.platform.startswith("linux"):
        pf = "linux"
    elif sys.platform.startswith("cygwin"):
        pf = "linux"
    elif sys.platform.startswith("win32"):
        pf = "windows"
    else:
        raise Exception(f"unsupported platform {sys.platform}")

    return f"x86_64-{pf}"


def download(name, dest, build_date):
    build_date_fmt = build_date.format("YYYYMMDD")

    dest.mkdir(parents=True, exist_ok=True)
    out = cathod(
        "components",
        "--build-date",
        build_date_fmt,
        "--component",
        name,
        "--platform",
        current_platform(),
        "--download",
        cwd=dest,
        out_filter=str,
    )
    assert not out.startswith(
        "No component"
    ), f"{out.strip()}: {name}, {dest}, {build_date}"
    return next(dest.glob(f"{name}*-{build_date_fmt}-{current_platform()}-bin.tar.gz"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("component", type=str)
    ap.add_argument("to", type=Path)
    args = ap.parse_args()

    print(download(args.component, args.to, pendulum.now().subtract(days=1)))
