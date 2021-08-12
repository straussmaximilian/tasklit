import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import sqlite3
import os
import subprocess
from functools import partial
from datetime import datetime, timedelta
import psutil
from multiprocessing import Process
import time

FORMAT = {'created':[], 'process id' : [], 'job name': [], 'command': [], 'last execution': [], 'running': []}


def run_job(command, name, logfile):
    with open(f"./logs/{logfile} {name}_stdout.txt", "wb") as out, open(f"./logs/{logfile} {name}_stderr.txt", "wb") as err:
        p = subprocess.Popen(command.split(' '), stdout=out, stderr=err)
        return p

def scheduler_process(command, name, logfile, start, timedelta, once):
    while True:
        now = datetime.now()
        if now > (start + timedelta):
            # Update database entry

            p = run_job(command, name, logfile)
            start += timedelta

        if once:
            break
        else:
            time.sleep(1)

def run_process(command, job_name):
    now = datetime.now()
    now_str = now.strftime("%d_%m_%Y %H:%M:%S")
    #FORMAT = {'created':[], 'process id' : [], 'job name': [], 'command': [], 'last execution': [], 'running': []}

    p = Process(target=scheduler_process, args=(command, name, logfile, start, timedelta, once))
    p.start()
    df = pd.DataFrame({'created':[now], 'process id' : [p.pid], 'job name': [job_name], 'command': [command], 'last execution': [], 'running': []})
    df.to_sql('processes', con=engine, if_exists='append', index=False)


def write_st_log(file):
    with open(file, "r", encoding='utf-8') as reader:
        log = reader.readlines()
        st.code(''.join(log))

def read_log(file):
    with open(file, "r", encoding='utf-8') as reader:
        log = reader.readlines()
        return log

def terminate_process(pid):
    try:
        parent = psutil.Process(pid)
        procs = parent.children(recursive=True)
        for p in procs:
            p.terminate()
        gone, alive = psutil.wait_procs(procs, timeout=3)
        for p in alive:
            p.kill()

        parent.terminate()
        parent.kill()
    except psutil.NoSuchProcess:
        pass

logfiles = os.listdir('./logs/')

engine = create_engine('sqlite:///data.db', echo=False)

st.write("# Tasklit")
st.text('A browser-based task scheduling system.')

#last log
try:
    df = pd.read_sql_table('processes', con=engine)
    df['running'] = df['process id'].apply(lambda x: psutil.pid_exists(x))
except ValueError:
    df = pd.DataFrame(FORMAT)

st.table(df)


if (len(df) > 0) and (df['process running']==False).sum() > 0:
    if st.button('Remove processes that are not running.'):
        running = df[df['process running']]
        running.to_sql('processes', con=engine, if_exists='replace', index=False)
        raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))


st.write('## New task')
job_name = st.text_input('Job name', 'Task')
command = st.text_input('Enter command','ping 8.8.8.8 -c 5')


if (command != '') and st.button('Test command'):
    st.info(f"Running '{command}'")
    with open(f"./logs/stdout.txt", "wb") as out, open(f"./logs/stderr.txt", "wb") as err:
        p = subprocess.Popen(command.split(' '), stdout=out, stderr=err)

    stdout = st.empty()
    stderr = st.empty()

    stop = st.checkbox("Stop")

    while True:
        poll = p.poll()
        stdout.code(''.join(read_log('./logs/stdout.txt')))
        stderr.code(''.join(read_log('./logs/stderr.txt')))
        if stop or poll is not None:
            terminate_process(p.pid)
            break

col1, col2, col3 = st.beta_columns(3)

frequency = col1.selectbox(
    'Select Frequency',
    ('Once', 'Interval', 'Timepoint'))

max_value_dict = {}
max_value_dict['Minutes'] = 59
max_value_dict['Hours'] = 59
max_value_dict['Days'] = 364
max_value_dict['Weeks'] = 51


if frequency == 'Interval':
    unit = col2.selectbox(
        'Select Unit',
        ('Minutes', 'Hours', 'Days', 'Weeks'))

    quantity = col3.slider(f'Every x {unit}', min_value = 1, max_value = max_value_dict[unit])

if frequency == 'Timepoint':
    weekdays = col2.multiselect('Select weekdays:', options=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], default = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])

c1, c2, c3 = st.beta_columns(3)

execution = c1.selectbox(
    'Execution',
    ('Now','Scheduled'))

if execution == 'Scheduled':
    date = c2.date_input('Starting date', datetime.now())
    time = c3.slider("Timepoint", min_value = datetime(2020, 1, 1, 00, 00), max_value = datetime(2020, 1, 1, 23, 59), value=datetime(2020, 1, 1, 12, 00), format="HH:mm")
    td_ = time - datetime(2020, 1, 1, 00, 00)
    start = date + td_

    st.write(start)

if st.button('Submit'):
    #p = run_process(command, job_name, start, timedelta)
    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))

if st.button('Refresh'):
    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))
