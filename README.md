[![codecov](https://codecov.io/gh/SecretLake/test-ci/branch/master/graph/badge.svg?token=6ZZHPQ76OO)](https://codecov.io/gh/SecretLake/test-ci)
![tests](https://github.com/SecretLake/test-ci/actions/workflows/run_unittests_and_linting.yml/badge.svg?branch=main)


# tasklit
A browser-based task scheduling app build on streamlit.
![Demo](assets/demo.gif)

## How to use?

Too lazy to write cronjobs? Working on a headless system and want to have a GUI?
`Tasklit` is a simple task scheduling application that allows you to schedule different processes via browser interface.

### Get started
* install requirements (streamlit)
* run the server `streamlit run app/main.py`
* visit the website (default is `http://localhost:8501` or network ip)
* Submit a new task. Example to run a test script on your desktop on a Mac system: `python \Users\username\Desktop\myscript.py`

## Limitations
* Only task execution, no logic based on return values

## Planned
* Notifications (Email, Slack, Teams)

## Tests
* Run tests via
  ```coverage run -m unittest discover tests```
* Check test coverage via ```coverage report -m```
 