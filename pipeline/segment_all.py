"""Segment every rendered page in parallel."""
import glob
import os
from concurrent.futures import ProcessPoolExecutor

from ink import RENDER
from segment import process


def run(p):
    process(p)
    return p


if __name__ == "__main__":
    pages = sorted(int(os.path.basename(f)[1:4]) for f in glob.glob(f"{RENDER}/p*.png"))
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        for p in ex.map(run, pages):
            pass
    print(len(pages), "pages segmented")
