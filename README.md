[![codecov](https://codecov.io/gh/straussmaximilian/tasklit/branch/main/graph/badge.svg?token=BW3L9GQ7M1)](https://codecov.io/gh/straussmaximilian/tasklit)
![tests](https://github.com/straussmaximilian/tasklit/actions/workflows/run_unittests_and_linting.yml/badge.svg?branch=main)


# tasklit
A browser-based task scheduling app build on streamlit.
![Demo](assets/demo.gif)

## How to use?

Too lazy to write cronjobs? Working on a headless system and want to have a GUI?
`Tasklit` is a simple task scheduling application that allows you to schedule different processes via browser interface.

### Get started

* create an environment `conda create --name tasklit python=3.8`
* install with `pip install .` or `pip install -e .` for the editable version
* run with `tasklit`
* visit the website (default is `http://localhost:8501` or network ip)
* Submit a new task. Example to run a test script on your desktop on a Mac system: `python \Users\username\Desktop\myscript.py`

To install with the development requirements install:
* install `pip install .[develop]`

## Limitations
* Only task execution, no logic based on return values

## Planned
* Notifications (Email, Slack, Teams)

## Acknowledgements
The PyPi workflow and installation routine is largely copied form the [AlphaTims](https://github.com/MannLabs/alphatims)- repository.

## Tests
* Run tests via
  ```coverage run -m unittest discover tests```
* Check test coverage via ```coverage report -m```
