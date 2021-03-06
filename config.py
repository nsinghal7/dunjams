# NOTE: add a file called dunjams/environment.py containing just the line:
# ENVIRONMENT = "name of your environment"
# and make sure your environment name is defined below.
# Don't push environment.py to the repo, since we all need a different copy
from environment import ENVIRONMENT # THIS MUST EXIST, BUT DON'T PUSH IT TO REPO

# TODO: define other environments and calibrate values
HALF_BEAT_TICKS = 240
POP_THRESHOLD_RATIO = 1.0
if ENVIRONMENT == 'mac':
    EPSILON_BEFORE = 40 / 960
    EPSILON_AFTER = 140 / 960
    SILENCE_THRESHOLD = -50
elif ENVIRONMENT == '4-270':
    EPSILON_BEFORE = 40 / 960
    EPSILON_AFTER = 180 / 960
    SILENCE_THRESHOLD = -20
    POP_THRESHOLD_RATIO = .6
elif ENVIRONMENT == 'windows':
    EPSILON_BEFORE = 40 / 960
    EPSILON_AFTER = 160 / 960
    SILENCE_THRESHOLD = -50
    HALF_BEAT_TICKS = 300
elif ENVIRONMENT == 'elinas windows':
    EPSILON_BEFORE = 40 / 960
    EPSILON_AFTER = 160 / 960
    SILENCE_THRESHOLD = -70
    HALF_BEAT_TICKS = 300
else:
    EPSILON_BEFORE = 40 / 960
    EPSILON_AFTER = 160 / 960
    SILENCE_THRESHOLD = -70
