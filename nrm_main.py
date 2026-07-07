#!/usr/bin/env python3
"""
Entry point utama NRM (Nirvana Reader MD).
File ini adalah target yang dikompilasi oleh Nuitka menjadi binary.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nrm.app import main

if __name__ == "__main__":
    sys.exit(main())
