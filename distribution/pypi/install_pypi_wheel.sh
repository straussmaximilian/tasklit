conda create -n tasklit_pip_test python=3.8 -y
conda activate tasklit_pip_test

pip install "tasklit"
tasklit
conda deactivate
