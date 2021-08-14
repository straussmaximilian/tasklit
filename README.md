# tasklit
A browser-based task scheduling app build on streamlit.
![Demo](demo.gif)

## How to use?

Too lazy to write cronjobs? Working on a headless system and want to have a GUI?
`Tasklit` is a simple task scheduling application that allows you to schedule different processes via browser interface.

### Get started
* install requirements (streamlit)
* run the server `streamlit run app.py`
* visit the website (default is `http://localhost:8501` or network ip)
* Submit a new task. Example to run a test script on your desktop on a Mac system: `python \Users\username\Desktop\myscript.py`

## Limitations
* Only task execution, no logic based on return values

## Planned
* Notifications (Email, Slack, Teams)
