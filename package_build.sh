#!/bin/bash
source /home/rmucsc.rm.unicatt.it/sb001956/TOTALRadiomics/lang_shift/venv/bin/activate
python3 setup.py bdist_wheel
pip install dist/vtg_km-1.0.0-py3-none-any.whl --force-reinstall
