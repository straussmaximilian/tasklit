import tasklit

from setuptools import setup, find_packages


with open("requirements.txt") as requirements_file:
    requirements = [_ for _ in requirements_file]

with open("requirements_dev.txt") as requirements_file:
    extra_requirements = {'develop': [_ for _ in requirements_file]}

with open("README.md", "r") as readme_file:
    LONG_DESCRIPTION = readme_file.read()

setup(
    name='tasklit',
    version='0.0.4',
    url='https://github.com/straussmaximilian/tasklit',
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author='Maximilian Strauss, Artem Vorobyev',
    author_email='straussmaximilian@gmail.com',
    description='A task scheduling app build on streamlit.',
    packages=find_packages(),
    install_requires=requirements,
    extras_require=extra_requirements,
    entry_points={
        "console_scripts": ["tasklit=tasklit.__main__:run"],
    },
)
