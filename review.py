import gitlab
import argparse
import os
from epycs.subprocess import cmd
from pathlib import Path
import zipfile


DEFAULT_GPR_FILE = "tictactoe/gnatsas.gpr"
ROOT = Path(__file__).resolve().parent


def current_git_branch():
    return cmd.git("branch", "--show-current", out_filter=lambda s: s.strip())


class ReviewApp:
    def __init__(self, instance, private_token, project_name, branch, gpr):
        self.gl = gitlab.Gitlab(instance, private_token=private_token)

        self.project = self.gl.projects.get(project_name)
        self.branch = branch
        self.branch_as_version = self.branch.replace("/", "-")[:63]
        self.gpr = ROOT / gpr
        self.prj_dir = self.gpr.parent

    def init(self):
        print(f"init for {self.branch}")
        all_pkg = reversed(list(self.project.packages.list(iterator=True)))
        for pkg in all_pkg:
            branch = pkg.version
            if branch == self.branch_as_version:
                self.download_analysis(pkg)
                break
        else:
            raise Exception(f"analysis not found for {self.branch}")

    def download_analysis(self, pkg):
        obj_dir = Path(self.prj_dir / "reviews")
        obj_dir.mkdir(exist_ok=True)

        filename = "gnatsas_analysis.zip"
        dest = obj_dir / filename

        print("download analysis for", pkg.version, pkg.created_at, "to", dest)
        pkg_bin = self.project.generic_packages.download(
            package_name=pkg.name, package_version=pkg.version, file_name=filename
        )

        with open(dest, "wb") as f:
            f.write(pkg_bin)

        print("extract to current project")
        zipf = zipfile.ZipFile(dest)
        zipf.extractall(path=self.prj_dir)

        self.show()

    def show(self):
        def color_cpm_to_text(s):
            for l in s.splitlines():
                cats = [c for c in l.split(":")[3].split() if c]
                if "high" in cats:
                    color = 31
                else:
                    color = 0
                print(f"\033[{color}m{l}\033[0m")

        cmd.gnatsas("report", "-P", self.gpr, out_filter=color_cpm_to_text)

    def edit(self):
        os.system(
            f'gnatstudio -P {self.gpr} --eval="python:GPS.execute_action(\\"gnatsas display code review\\")"'
        )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "command", choices=["init", "show", "edit"], nargs="?", default="init"
    )
    ap.add_argument("--project", "-P", default=DEFAULT_GPR_FILE)
    args = ap.parse_args()

    pat = os.environ.get("GITLAB_TOKEN")
    if pat is None:
        # AdaCore's e3 specific
        from e3.auth.gitlab import gen_gitlab_token

        pat = gen_gitlab_token()

    review = ReviewApp(
        "https://gitlab.adacore-it.com",
        private_token=pat,
        project_name="eng/codepeer/gitlab-workflow",
        branch=current_git_branch(),
        gpr=args.project,
    )

    getattr(review, args.command)()
