#!/usr/bin/env bash
if [ "$#" -gt 0 ]; then 
	python -m unittest discover "$1"
else
	python -m unittest discover src/tests
fi
