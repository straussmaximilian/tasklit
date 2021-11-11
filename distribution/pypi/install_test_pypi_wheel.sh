conda create -n tasklit_pip_test python=3.8 -y
conda activate tasklit_pip_test
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple "tasklit"
#tasklit #TODO: this would run until infinity
conda deactivate
