# NOTE: add a file called dunjams/environment.py containing just the line:
# ENVIRONMENT = "name of your environment"
# and make sure your environment name is defined below.
# Don't push environment.py to the repo, since we all need a different copy
from environment import ENVIRONMENT # THIS MUST EXIST, BUT DON'T PUSH IT TO REPO

# TODO: define other environments and calibrate values
if ENVIRONMENT == 'mac':
    EPSILON_BEFORE = 40 / 960
    EPSILON_AFTER = 140 / 960
    SILENCE_THRESHOLD = -50
elif ENVIRONMENT == '4-270':
    EPSILON_BEFORE = 40 / 960
    EPSILON_AFTER = 180 / 960
    SILENCE_THRESHOLD = -20
elif ENVIRONMENT == 'windows':
    EPSILON_BEFORE = 40 / 960
    EPSILON_AFTER = 160 / 960
    SILENCE_THRESHOLD = -50
else:
    EPSILON_BEFORE = 40 / 960
    EPSILON_AFTER = 160 / 960
    SILENCE_THRESHOLD = -70
