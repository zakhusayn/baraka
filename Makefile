# Makefile for setting up and running the Baraka Streamlit dashboard
.PHONY: all setup run clean

all: setup run

setup:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

run:
	. venv/bin/activate && streamlit run Dashboard.py

clean:
	rm -rf venv
