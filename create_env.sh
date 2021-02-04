#!/bin/bash
# could add this script to "npm run build"
# but would make it complicated to read.
# for now we just need to manually run this
cd lib
python3 -m venv twitterVenv
source twitterVenv/bin/activate
pip uninstall requests
pip install requests==2.25.1
pip install urllib3==1.26.2
pip install boto3==1.17.4
pip install tweepy