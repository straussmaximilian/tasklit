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
import random

FORMAT = {'task_id':[],'created':[], 'process id' : [], 'job name': [], 'command': [], 'last update': [], 'running': []}

task_names = ['Mimas', 'Enceladus', 'Tethys', 'Dione', 'Rhea', 'Titan', 'Iapetus']

time_values = {}
time_values['Minutes'] = 59
time_values['Hours'] = 59
time_values['Days'] = 364
time_values['Weeks'] = 51

date_translation = {}
date_translation['Days'] = timedelta(days=1)
date_translation['Hours'] = timedelta(hours=1)
date_translation['Minutes'] = timedelta(minutes=1)
date_translation['Weeks'] = timedelta(weeks=1)


days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
day_lookup = {i:_ for i, _ in enumerate(days)}

BASE_LOG_DIR = "./logs/"
DEFAULT_LOG_DIR_OUT = f"{BASE_LOG_DIR}stdout.txt"
DEFAULT_LOG_DIR_ERR = f"{BASE_LOG_DIR}stderr.txt"

def try_cmd(command:str):
    st.info(f"Running '{command}'")

    with open(DEFAULT_LOG_DIR_OUT, "wb") as out, open(DEFAULT_LOG_DIR_ERR, "wb") as err:
        p = subprocess.Popen(command.split(' '), stdout=out, stderr=err)

    stdout = st.empty()
    stderr = st.empty()

    stop = st.checkbox("Stop")

    while True:
        poll = p.poll()
        stdout.code(''.join(read_log(DEFAULT_LOG_DIR_OUT)))
        stderr.code(''.join(read_log(DEFAULT_LOG_DIR_ERR)))
        if stop or poll is not None:
            terminate_process(p.pid)
            break

def select_date():

    col1, col2, col3 = st.beta_columns(3)

    frequency = col1.selectbox(
        'Select Frequency',
        ('Once', 'Interval', 'Daily'))

    if frequency == 'Interval':
        unit = col2.selectbox(
            'Select Unit',
            ('Minutes', 'Hours', 'Days', 'Weeks'))
        quantity = col3.slider(f'Every x {unit}', min_value = 1, max_value = time_values[unit])
    else:
        unit = None
        quantity = None

    if frequency == 'Daily':
        weekdays = col2.multiselect('Select weekdays:', options=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], default = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
    else:
        weekdays = None

    c1, c2, c3 = st.beta_columns(3)

    execution = c1.selectbox(
        'Execution',
        ('Now','Scheduled'))

    if execution == 'Scheduled':
        date = c2.date_input('Starting date', datetime.now())
        time = c3.slider("Timepoint", min_value = datetime(2020, 1, 1, 00, 00), max_value = datetime(2020, 1, 1, 23, 59), value=datetime(2020, 1, 1, 12, 00), format="HH:mm")
        date = datetime(date.year, date.month, date.day)
        td_ = time - datetime(2020, 1, 1, 00, 00, 00)
        start = date + td_
        if frequency == 'Daily':
            while day_lookup[start.weekday()] not in weekdays:
                start += timedelta(days=1)
    else:
        start = datetime.now()

    start_dt = start.strftime("%d/%m/%Y, %H:%M:%S")
    st.text(f"Scheduled first execution {start_dt}")

    return start, unit, quantity, weekdays, frequency, execution


def run_job(command: str, job_name):
    with open(f"{BASE_LOG_DIR}{job_name}_stdout.txt", "ab") as out, open(f"{BASE_LOG_DIR}{job_name}_stderr.txt", "ab") as err:
        p = subprocess.Popen(command.split(' '), stdout=out, stderr=err)
        return p


def check_weekday(now, weekdays):
    """
    Check if function should be executed based on the weekday
    """

    if weekdays is None:
        return True #Always execute if this is none
    else:
        if day_lookup[now.weekday()] in weekdays:
            return True
        else:
            return False

def write_execution_log(job_name, command, now, msg):
    now_str = now.strftime("%d_%m_%Y %H:%M:%S")
    for suffix in ['.txt','_stdout.txt', '_stderr.txt']:
        with open(f"{BASE_LOG_DIR}{job_name}{suffix}", "a") as file:
            file.write(f"--- {msg} {command} at {now_str} ---\n")

def scheduler_process(command, job_name, start, unit, quantity, weekdays, frequency, execution, task_id):

    if frequency == 'Once':
        write_execution_log(job_name, command, datetime.now(), 'Started')
        p = run_job(command, job_name)
        write_execution_log(job_name, command, datetime.now(), 'Finished')
    else:
        if weekdays is not None:
            timedelta = datetime.timedelta(days=1)
        else:
            timedelta = date_translation[unit]*quantity

        if execution == 'Now':
            start -= timedelta

        while True:
            now = datetime.now()
            if check_weekday(now, weekdays) and (now > (start + timedelta)):
                # Write Execution
                write_execution_log(job_name, command, now, 'Started')
                p = run_job(command, job_name)
                p.wait()
                start += timedelta
            else:
                time.sleep(1)

def run_process(command, job_name, start, unit, quantity, weekdays, frequency, execution, task_id):

    #st.write(command, job_name, start, unit, quantity, weekdays, frequency, task_id)
    created = datetime.now()#.strftime("%d_%m_%Y %H:%M:%S")
    #FORMAT = {'created':[], 'process id' : [], 'job name': [], 'command': [], 'last update': [], 'running': []}

    p = Process(target=scheduler_process, args=(command, job_name, start, unit, quantity, weekdays, frequency, execution, task_id))
    p.start()
    df = pd.DataFrame({'task_id':[task_id], 'created':[created], 'process id' : [p.pid], 'job name': [job_name], 'command': [command], 'last update': [None], 'running': [None]})
    df.to_sql('processes', con=engine, if_exists='append', index=False)
    #FORMAT = {'task_id':[],'created':[], 'process id' : [], 'job name': [], 'command': [], 'last update': [], 'running': []}


def write_st_log(file):
    with open(file, "r", encoding='utf-8') as reader:
        log = reader.readlines()
        st.code(''.join(log))

def read_log(file):
    with open(file, "r", encoding='utf-8') as reader:
        log = reader.readlines()
        return log

def get_task_id(df):
    task_id = 0
    while task_id in df['task_id'].to_list():
        task_id +=1

    return task_id

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

## Main interface

logfiles = os.listdir(f'{BASE_LOG_DIR}')
engine = create_engine('sqlite:///data.db', echo=False)

st.write("# 🕙 Tasklit")
st.text('A browser-based task scheduling system.')

#last log
try:
    df = pd.read_sql_table('processes', con=engine)
    df['running'] = df['process id'].apply(lambda x: psutil.pid_exists(x))
except ValueError:
    df = pd.DataFrame(FORMAT)

st.table(df)

if (len(df) > 0) and (df['running']==False).sum() > 0:
    if st.button('Remove processes that are not running.'):
        running = df[df['running']]
        running.to_sql('processes', con=engine, if_exists='replace', index=False)
        raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))

with st.beta_expander('New task'):
    job_name = st.text_input('Job name', random.choice(task_names))
    command = st.text_input('Enter command','ping 8.8.8.8 -c 5')

    if (command != '') and st.button('Test command'):
        try_cmd(command)

    start, unit, quantity, weekdays, frequency, execution = select_date()

    task_id = get_task_id(df)

    if st.button(f'Submit'):
        p = run_process(command, job_name, start, unit, quantity, weekdays, frequency, execution, task_id)
        raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))

with st.beta_expander('Explore task'):
    st.selectbox('task_id', df['task_id'].unique())

if st.button('Refresh'):
    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))
