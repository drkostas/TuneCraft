# Makefile for COSC525-Project2
.ONESHELL:
SHELL=/bin/bash
PYTHON_VERSION=3.10
ENV_NAME=tune_craft

# You can use either venv (venv) or conda env
# by specifying the correct argument (env=<conda, venv>)
ifeq ($(env),venv)
	# Use Conda
	BASE=venv
	BIN=$(BASE)/bin
	CREATE_COMMAND="python$(PYTHON_VERSION) -m venv $(BASE)"
	DELETE_COMMAND="rm -rf $(BASE)"
	ACTIVATE_COMMAND="source venv/bin/activate"
	DEACTIVATE_COMMAND="deactivate"
else
	# Use Conda
	BASE=~/anaconda3/envs/$(ENV_NAME)
	BIN=$(BASE)/bin
	CREATE_COMMAND="conda create --prefix $(BASE) python=$(PYTHON_VERSION) -y"
	DELETE_COMMAND="conda env remove -p $(BASE)"
	ACTIVATE_COMMAND="conda activate -p $(BASE)"
	DEACTIVATE_COMMAND="conda deactivate"
endif

# To load a env file use env_file=<path to env file>
# e.g. make release env_file=.env
ifneq ($(env_file),)
	include $(env_file)
#	export
endif

all:
	$(MAKE) help
help:
	@echo
	@echo "-----------------------------------------------------------------------------------------------------------"
	@echo "                                              DISPLAYING HELP                                              "
	@echo "-----------------------------------------------------------------------------------------------------------"
	@echo "Use make <make recipe> [env=<conda|venv>] [env_file=<path to env file>]"
	@echo
	@echo "make help"
	@echo "       Display this message"
	@echo "make install [env=<conda|venv>] [env_file=<path to env file>]"
	@echo "       Call clean delete_conda_env create_conda_env setup tests"
	@echo "make clean [env=<conda|venv>] [env_file=<path to env file>]"
	@echo "       Delete all './build ./dist ./*.pyc ./*.tgz ./*.egg-info' files"
	@echo "make create_env [env=<conda|venv>] [env_file=<path to env file>]"
	@echo "       Create a new conda env or virtualenv for the specified python version"
	@echo "make delete_env [env=<conda|venv>] [env_file=<path to env file>]"
	@echo "       Delete the current conda env or virtualenv"
	@echo "-----------------------------------------------------------------------------------------------------------"
install:
	$(MAKE) delete_env
	$(MAKE) create_env
	$(MAKE) clean
	$(MAKE) requirements
	@echo -e "\033[0;31m############################################"
	@echo
	@echo "Installation Successful!"
	@echo "To activate the conda environment run:"
	@echo '    conda activate $(ENV_NAME)'
requirements:
	# conda install --file requirements.txt -y
	pip install -r requirements.txt
create_env:
	@echo "Creating virtual environment.."
	@eval $(CREATE_COMMAND)
delete_env:
	@echo "Deleting virtual environment.."
	@eval $(DELETE_COMMAND)

.PHONY: help install clean delete_env create_env requirements