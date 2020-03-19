#!/bin/bash
screen -dm -S "kolesa" bash -c "python3 kolesa.py; exec sh"
echo "kolesa started"
