import json
import argparse

def read_json(s):
    with open(s, "rt") as f:
        return json.load(f)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=read_json)
    args = ap.parse_args()

    for k, v in args.manifest.items():
        print("--build-arg", f"{k}={v}", end=" ")
