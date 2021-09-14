import os
import sys

from streamlit import cli as stcli

def run():
    _this_file = os.path.abspath(__file__)
    _this_directory = os.path.dirname(_this_file)

    file_path = os.path.join(_this_directory, 'app.py')

    args = ["streamlit", "run", file_path, "--global.developmentMode=false", "--server.port=8501", "--browser.gatherUsageStats=False"]
    sys.argv = args

    sys.exit(stcli.main())


if __name__ == '__main__':

    run()
