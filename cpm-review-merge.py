import argparse
from pathlib import Path
from subprocess import check_call


def get_args():
    ap = argparse.ArgumentParser(
        description="""This script is in charge of integrating the given CPR review file
onto the current analysis, modifying it so that it contains the new and updated
reviews.

Please note that no effort is made on making sure the analysis and the review
are compatible, in other words the CPR should have been generated from the current
CPM."""
    )

    ap.add_argument("review_file", help="CPR file to integrate", type=Path)

    return ap.parse_args()


ROOT = Path(__file__).resolve().parent


def get_current_cpm():
    # /!\ current analysis, but not current baseline
    return ROOT / "tictactoe" / "codepeer" / "codepeer.cpms" / "codepeer.4.cpm"


def move(frm, to):
    to.unlink()
    frm.rename(to)


def main():
    args = get_args()
    assert args.review_file.is_file()
    assert get_current_cpm().is_file()

    check_call(["cpm-review", str(get_current_cpm()), "--review-file", str(args.review_file)])
    cpmr = get_current_cpm().with_suffix(".r.cpm")
    move(cpmr, get_current_cpm())


if __name__ == "__main__":
    main()
