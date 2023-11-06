#!/bin/bash
source /home/rmucsc.rm.unicatt.it/sb001956/TOTALRadiomics/lang_shift/venv/bin/activate  #CHANGE HERE
python3 setup.py bdist_wheel
pip install dist/vtg_km_he-1.0.0-py3-none-any.whl --force-reinstall
