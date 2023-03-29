import json
import shutil
import collections
import logging
import argparse
import epycs.subprocess as es
from pathlib import Path
from dockerfile import *

log = logging.getLogger("dockbuzz")

ROOT = Path(__file__).resolve().parent


docker = es.find_program("docker")
make = es.find_program("make")
download_from_cathod = es.cmd.python.arg(ROOT / "download_from_cathod.py")


def get_component_from_cathod(out, cathod_name):
    return download_from_cathod(cathod_name, out, out_filter=lambda s: out / s.strip())


class BuilderFromManifest:
    def __init__(self, content):
        self.manifest = content
        self.imports = self.manifest["with"]

    def download_component(self, out, name, component):
        if "cathod" in component:
            return get_component_from_cathod(out, component["cathod"])
        else:
            raise Exception(f"unknown source for {name}: {component}")

    def download_components(self, clean=False):
        out = ROOT / "obj"
        if clean and out.exists():
            log.warning(f"clean {out}")
            shutil.rmtree(out)
        out.mkdir(exist_ok=not clean)
        self.components = {
            name: self.download_component(out, name, component)
            for name, component in self.manifest["components"].items()
        }
        return self.components

    def resolve_image(self, full_path):
        split = full_path.split("/")
        prefix, suffix = split[0], split[1:]
        assert prefix in self.imports, prefix

        if prefix == "dockerhub":
            return "/".join(suffix)
        else:
            assert suffix[0] == "images", suffix[0]
            return "/".join(suffix[1:])

    def build_image(self, name, local_config, out):
        log.info(f"build {name}")
        df = Dockerfile(name)
        build = df.from_image(self.resolve_image(local_config["build_image"]), "build")
        run = df.from_image(self.resolve_image(local_config["run_image"]), "run")
        for c in local_config["components"]:
            tmp_docker_dest = Path("/tmp") / c
            install_docker_dest = Path("/opt") / c
            component_config = self.manifest["components"][c]
            package = tmp_docker_dest / self.components[c].name
            build.copy(self.components[c], package)
            build.install_component(
                c,
                tmp_docker_dest,
                package,
                install_docker_dest,
                component_config["install"],
            )
            run.copy_install(install_docker_dest, install_docker_dest, from_image=build)

        df.write(out / name, clean=False)

    def build_images(self, clean=False):
        out = ROOT / "images"
        if clean and out.exists():
            log.warning(f"clean {out}")
            shutil.rmtree(out)
        out.mkdir(exist_ok=not clean)
        for name, local_config in self.manifest["images"].items():
            self.build_image(name, local_config, out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    with open(args.manifest) as f:
        builder = BuilderFromManifest(json.load(f))
    components = builder.download_components()
    log.debug(f"components downloaded: {[c for c in components]}")
    builder.build_images()
