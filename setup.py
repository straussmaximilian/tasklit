from setuptools import setup, find_packages
import tasklit

with open("requirements.txt") as requirements_file:
    requirements = []
    for line in requirements_file:
        requirements.append(line)

setup(
    name='tasklit',
    version='0.0.1',
    url='https://github.com/straussmaximilian/tasklit',
    author='Maximilian Strauss, Artem Vorobyev',
    author_email='straussmaximilian@gmail.com',
    description='A task scheduling app build on streamlit.',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": ["tasklit=tasklit.__main__:run"],
    },
)
