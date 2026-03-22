import sys
import multiprocessing
from verba.cli import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
