import shutil
import collections
from pathlib import Path


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
                self.operations.append(
                    f"COPY --from={from_image.name} {component} {to}"
                )

        def copy_install(self, component, to, from_image=None):
            self.copy(component, to, from_image)
            self.operations.append(f'ENV PATH "{to}/bin:${{PATH}}"')

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
