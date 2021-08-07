import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import sqlite3
import os
import subprocess
from functools import partial
from datetime import datetime
import psutil
import schedule

#Creation date
#Process id
#String
#Log direction

#Notification settings
#Email
#Teams / Slack notification

def run_job(command, name, logfile):
    with open(f"./logs/{logfile} {name}_stdout.txt", "wb") as out, open(f"./logs/{logfile} {name}_stderr.txt", "wb") as err:
        p = subprocess.Popen(command.split(' '), stdout=out, stderr=err)
        return p

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
    df['process running'] = df['process'].apply(lambda x: psutil.pid_exists(x))
except ValueError:
    df = pd.DataFrame()

st.table(df)


if (len(df) > 0) and (df['process running']==False).sum() > 0:
    if st.button('Remove unused processes.'):
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

frequency = st.selectbox(
    'Select Frequency',
    ('Once','Daily', 'Weekly', 'Monthly'))

if frequency != 'Once':
    date = st.date_input('Starting date', datetime.now())
    time = st.slider("Timepoint", min_value = datetime(2020, 1, 1, 00, 00), max_value = datetime(2020, 1, 1, 23, 59), value=datetime(2020, 1, 1, 12, 00), format="HH:mm")

if st.button('Submit'):
    now = datetime.now()
    now_str = now.strftime("%d_%m_%Y %H:%M:%S")
    p = run_job(command, job_name, now_str)
    df = pd.DataFrame({'created':[now], 'process' : [p.pid], 'job_name': [job_name], 'command': [command]})
    st.write(df)
    df.to_sql('processes', con=engine, if_exists='append', index=False)
    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))

if False:
    if len(logfiles) == 0:
        st.info('No logfiles present.')
        option = None
    else:
        option = st.selectbox('Read log', logfiles)

    if option:
        st.write(option)
        write_st_log('./logs/'+option)
        #write_st_log('stderr.txt')
