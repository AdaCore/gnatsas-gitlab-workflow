import re
import json
import shutil
import collections
import logging
import epycs.subprocess as es
from pathlib import Path

log = logging.getLogger("dockbuzz")

ROOT = Path(__file__).resolve().parent


docker = es.find_program("docker")
make = es.find_program("make")
download_from_cathod = es.cmd.python.arg(ROOT / "download_from_cathod.py")

def get_component_from_cathod(out, cathod_name):
    return download_from_cathod(cathod_name, out, out_filter=lambda s : out / s.strip())

class Dockerfile:
    def __init__(self, name):
        self.name = name
        self.images = collections.OrderedDict()

    class Image:
        def __init__(self, parent, name):
            self.name = name
            if name is not None:
                self.operations = [f"FROM {parent} AS {name}"]
            else:
                self.operations = [f"FROM {parent}"]

        def copy(self, component, to, from_image=None):
            if from_image is None:
                def copy_(out):
                    shutil.copy(component, out / component.name)
                    return f"COPY {component.name} {to}"
                self.operations.append(copy_)
            else:
                self.operations.append(f"COPY --from={from_image.name} {component} {to}")

        def copy_install(self, component, to, from_image=None):
            self.copy(component, to, from_image)
            self.operations.append(f"ENV PATH \"{to}/bin:${{PATH}}\"")

        def install_component(self, name, tmp, package, to, config):
            def param_and_escape(s):
                s = s.format(prefix=to)
                s = s.replace("\n", "\\n")
                return s
            doinstall_pipe = param_and_escape(config["doinstall_pipe"])

            cmd = f"""RUN set -xe \\
    && cd {tmp.parent} \\
    && mkdir -p {name} \\
    && tar xf {package} --strip-components 1 -C {name} \\
    && cd {name} \\
    && echo \"{doinstall_pipe}\" | ./doinstall """ 

            if "remove" in config:
                cmd += f"\\\n    && cd {to} "
                keep = f"/tmp/{to.name}.keep/"
                for k in config.get("keep", []):
                    cmd += f"\\\n    && mkdir -p {keep}/{k} && mv {k} {keep} "

                for rm in config["remove"]:
                    cmd += f"\\\n    && rm -rf {rm} "

                for k in config.get("keep", []):
                    cmd += f"\\\n    && mv {keep}/{k} {k} \\\n    && rm -rf {keep} "
            cmd += f"\\\n    && rm -rf {tmp} "

            self.operations.append(cmd)

        def write(self, out, f):
            for op in self.operations:
                if callable(op):
                    f.write(op(out))
                else:
                    f.write(op)
                f.write("\n")

    def from_image(self, parent, named_as=None):
        self.images[named_as] = self.Image(parent, named_as)
        return self.images[named_as]

    def write(self, out, clean):
        if clean and out.exists():
            shutil.rmtree(out)
        out.mkdir(exist_ok=not clean)
        with open(out / "Dockerfile", "wt") as f:
            print("# This file has been automatically generated", file=f)
            for name, o in self.images.items():
                print("", file=f)
                o.write(out, f)

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
            name : self.download_component(out, name, component)
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
            build.install_component(c, tmp_docker_dest, package, install_docker_dest, component_config["install"])
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
    logging.basicConfig(level=logging.DEBUG)
    with open(ROOT / "manifest.json") as f:
        builder = BuilderFromManifest(json.load(f))
    components = builder.download_components()
    log.debug(f"components downloaded: {[c for c in components]}")
    builder.build_images()
