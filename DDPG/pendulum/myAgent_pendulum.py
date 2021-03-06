import signal, os
from replayBuffer import *
import gym
import tensorflow as tf
from tensorflow.keras import layers
import numpy as np
import matplotlib.pyplot as plt

allReward = [] # List of rewards over time, for logging and visualization
useNoise = True

"""Signal handler displays the agent's progress"""
def handler1(signum, frame):

    # Plot the data
    plt.plot(allReward)
    plt.ylabel('Cumulative Reward')
    plt.xlabel('Episode')
    plt.show()

    myAgent.epsilon_min = 0.00001

    useNoise = False

signal.signal(signal.SIGTSTP, handler1)


class Agent():
    
    def __init__(self):
     
        # Hyper-parameters
        self.discount = 0.99
        self.memorySize = 50000
        self.batch_size = 64 # Mini batch size for keras .fit method

        self.moveNumber = 0 # Number of actions taken in the current episode 
        self.save = 50 # This describes how often to save each network to disk  

        self.currentGameNumber = 0 
        self.cumulativeReward = 0 # Current game's total reward
        
        # These parameters are Specefic to Pendulum-V0!!
        self.max_control_signal = 2.0
        self.lowerLimit = -2.0
        self.upperLimit = 2.0

        self.env = gym.make('Pendulum-v0')
        self.state = self.env.reset()
        
        self.polyak_rate = 0.005
        self.action_space_size = 1 # Size of the action vector  
        self.state_space_size = 3 # Size of the observation vector
        
        self.replayMemory = replayBuffer(self.memorySize, self.state_space_size, self.action_space_size)

        self.actor = self.defineActor()
        self.actor_target = self.defineActor()
        
        self.critic = self.defineCritic()
        self.critic_target = self.defineCritic()

        self.actor_target.set_weights(self.actor.get_weights())
        self.critic_target.set_weights(self.critic.get_weights())
        
        self.critic_learning_rate = 0.002
        self.actor_learning_rate = 0.001

        self.critic_optim = tf.keras.optimizers.Adam(self.critic_learning_rate)
        self.actor_optim = tf.keras.optimizers.Adam(self.actor_learning_rate)

        std_dev = 0.2
        self.init_noise_process(average = np.zeros(1), std_dev = float(std_dev) * np.ones(1))

   
    def defineActor(self):

        actor_initializer = tf.random_uniform_initializer(minval = -0.003, maxval = 0.003)

        inputs = layers.Input(shape = (self.state_space_size, ))

        nextLayer = layers.Dense(256, activation = "relu")(inputs)
        nextLayer = layers.Dense(256, activation = "relu")(nextLayer)
        
        # tanh maps into the interval of [-1, 1]
        outputs = layers.Dense(1, activation = "tanh", kernel_initializer = actor_initializer)(nextLayer)

        # max_control signal is 2.0 for Pendulum.
        outputs = outputs * self.max_control_signal
        return tf.keras.Model(inputs, outputs)
    
    def defineCritic(self):
       
        state_inputs = layers.Input(shape=(self.state_space_size))
        state_stream = layers.Dense(16, activation="relu")(state_inputs)
        state_stream = layers.Dense(32, activation="relu")(state_stream)

        action_inputs = layers.Input(shape = (self.action_space_size) )
        action_stream = layers.Dense(32, activation="relu")(action_inputs)

        # Merge the two seperate information streams
        merged_stream = layers.Concatenate()([state_stream, action_stream])

        merged_stream = layers.Dense(256, activation="relu")(merged_stream)
        merged_stream = layers.Dense(256, activation="relu")(merged_stream)
        outputs = layers.Dense(1)(merged_stream)

        return tf.keras.Model([state_inputs, action_inputs], outputs)
    
    """Describe"""
    def init_noise_process(self, average, std_dev, theta = 0.15, dt = 0.01, x_start = None):
    
        self.theta = theta
        self.average = average
        self.std_dev = std_dev
        self.dt = dt
        self.x_start = x_start
        self.x_prior = np.zeros_like(self.average)
        # self.reset()
       
    def noise(self):
        noise = (self.x_prior + self.theta * (self.average - self.x_prior) * self.dt + self.std_dev * np.sqrt(self.dt) * np.random.normal(size=self.average.shape) )
        
        self.x_prior = noise
        return noise


    def chooseAction(self, state):

        state = tf.expand_dims(tf.convert_to_tensor(state), 0)
        action = self.actor(state)

        # FIX me - generate noise
        noise = self.noise()
        if (useNoise == True):
            action = action.numpy() + noise
        else:
            action = action.numpy()


        # Make sure action is withing legal range
        action = np.clip(action, self.lowerLimit, self.upperLimit)

        return [np.squeeze(action)]

    
    # Eager execution is turned on by default in TensorFlow 2. Decorating with tf.function allows
    # TensorFlow to build a static graph out of the logic and computations in our function.
    # This provides a large speed up for blocks of code that contain many small TensorFlow operations such as this one.
    @tf.function
    def update(
        self, states, actions, rewards, next_states,
    ): 
    
    #def update(self, states, actions, rewards, next_states):

        with tf.GradientTape() as tape:
            
            target_actions = self.actor(next_states, training = True)
            
            predicted_values = rewards + self.discount * self.critic([next_states, target_actions], training = True)
            
            critic_value = self.critic([states, actions], training = True)
            
            critic_loss = tf.math.reduce_mean(tf.math.square(predicted_values - critic_value))

        critic_grad = tape.gradient(critic_loss, self.critic.trainable_variables)
        self.critic_optim.apply_gradients( zip(critic_grad, self.critic.trainable_variables) )

        with tf.GradientTape() as tape:
            
            actions = self.actor(states, training = True)
            critic_value = self.critic([states, actions], training = True)
            # Remember to negate the loss!
            actor_loss = -tf.math.reduce_mean(critic_value)
                
        actor_grad = tape.gradient(actor_loss, self.actor.trainable_variables)
        self.actor_optim.apply_gradients(zip(actor_grad, self.actor.trainable_variables))
        
    def train(self):
        
        states, actions, rewards, next_states = self.replayMemory.sample(self.batch_size) 

        # Convert to Tensorflow data types
        states  = tf.convert_to_tensor(states)
        actions = tf.convert_to_tensor(actions)
        rewards = tf.cast(tf.convert_to_tensor(rewards), dtype = tf.float32)

        next_states = tf.convert_to_tensor(next_states)

        self.update(states, actions, rewards, next_states)


    def handleGameEnd(self):

        print("Game number " + str(self.currentGameNumber) + " ended with a total reward of " + str(self.cumulativeReward))
        allReward.append(self.cumulativeReward)
        self.cumulativeReward = 0

        self.currentGameNumber = self.currentGameNumber + 1

"""Polyak averaging from online network to the target network"""
@tf.function
def update_target(target_weights, online_weights, polyak_rate):

    for (target, online) in zip(target_weights, online_weights):
        target.assign(online * polyak_rate + target * (1 - polyak_rate))


#tf.compat.v1.enable_eager_execution()
myAgent = Agent()    

while (True): 
    current_state = myAgent.env.reset()
    std_dev = 0.1 #0.2
    myAgent.init_noise_process(average = np.zeros(1), std_dev = float(std_dev) * np.ones(1))

    while(True):
        myAgent.env.render()

        action = myAgent.chooseAction(current_state)
        
        # observation, reward, done, info
        next_state, reward, done, info = myAgent.env.step(action)
    
        # state, action, reward, next_state
        myAgent.replayMemory.append(current_state, action, reward, next_state)

        # Update counters
        myAgent.moveNumber = myAgent.moveNumber + 1
        myAgent.cumulativeReward = myAgent.cumulativeReward + reward

        update_target(myAgent.actor_target.variables, myAgent.actor.variables, myAgent.polyak_rate)
        update_target(myAgent.critic_target.variables, myAgent.critic.variables, myAgent.polyak_rate)

        current_state = next_state

        if (done == True):
            myAgent.handleGameEnd()
            break

        if (myAgent.currentGameNumber > 2):
            myAgent.train()
        

