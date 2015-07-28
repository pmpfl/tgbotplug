import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='tgbotplug',
    version='0.1.7',
    packages=['tgbot'],
    include_package_data=True,
    license='MIT License',
    description='Telegram plugin-based bot',
    long_description=README,
    url='https://github.com/fopina/tgbotplug',
    author='Filipe Pina',
    author_email='fopina@skmobi.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=[
        'requests==2.7.0',
        'twx.botapi==1.0.2',
        'peewee==2.6.3',
    ]
)
