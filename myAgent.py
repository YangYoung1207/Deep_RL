import numpy as np
import time
import random
import sys
import os
import gym
import warnings
from PIL import Image
import cv2
from dataInstance import *
from observation import *

warnings.filterwarnings('ignore') # Gets rid of future warnings
with warnings.catch_warnings():
    from keras.layers import Activation, Dense, Flatten, Conv2D
    from keras.models import Sequential
    from keras.optimizers import RMSprop, Adam
    import numpy as np
    import tensorflow as tf
    from tensorflow import keras
    import matplotlib.pyplot as plt
    from tensorflow.python.util import deprecation
    deprecation._PRINT_DEPRECATION_WARNINGS = False
    tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

# Globals
downSizedLength = 64
downSizedWidth = 64

# These are the most recently seen observations 
observationT1 = None
observationT2 = None
observationT3 = None
observationT4 = None
observationT5 = None

# In order to make room for the next observation, move
# back each one in the "queue"
def reorderObservations():
    global observationT1
    global observationT2
    global observationT3
    global observationT4
    global observationT5
    
    observationT5 = observationT4
    observationT4 = observationT3
    observationT3 = observationT2
    observationT2 = observationT1
 

# Generate the first three frames so we can perform an action
# We need 4 frames to use the nueral network
# Input: void
# Return: void
def generateFirst3Frames():
    global observationT1
    global observationT2
    global observationT3
    global observationT4
    global observationT5

    env.render()
    action = env.action_space.sample()
    state, reward, done, info = env.step(action)
    observationT3 = observation(state)
        
    env.render()
    action = env.action_space.sample()
    state, reward, done, info = env.step(action)
    observationT2 = observation(state)

    env.render()
    action = env.action_space.sample()
    state, reward, done, info = env.step(action)
    observationT1 = observation(state)


# Define the two neural networks for Double Deep Q Learning
QA = Sequential()
QA.add(Flatten())

QB = Sequential()
QB.add(Dense(48, input_dim = downSizedLength * downSizedWidth, activation = 'relu'))
QB.add(Dense(24, activation = 'relu'))
QB.add(Dense(4, activation = 'linear'))
QB.compile(loss = 'mse',  optimizer = Adam(lr = 0.001) )


# Creates enviroment from OpenAI gym
env = gym.make('Breakout-v0')

state = env.reset()

# Discrete(4)
# print(env.action_space)

# Box(210, 160, 3)
# print(env.observation_space)

# Generate the first three frames so we can perform an action
# We need 4 frames to use the nueral network
generateFirst3Frames()

while(True):
    env.render()
    action = env.action_space.sample()
    state, reward, done, info = env.step(action)

    reorderObservations()
    observationT1 = observation(state) 
    
    # Turn most recent 4 observations into a training instance  
    myDataInstance = dataInstance(observationT1, observationT2, observationT3, observationT4)
    myDataInstance.viewAllImages()
    
    # QA.predict(observation) 


while (True):
    continue

    # time.sleep(0.2)
