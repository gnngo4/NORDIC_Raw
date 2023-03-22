#!/bin/bash

# Compile nordic
mcc -m nordic_main.m -m NIFTI_NORDIC.m -R -nojvm -d nordic_compiled -v
