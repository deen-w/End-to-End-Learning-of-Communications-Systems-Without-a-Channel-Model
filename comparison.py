#!/usr/bin/env python
# coding: utf-8

# ## Importing Packages

# In[1]:


import numpy as np 
import matplotlib.pyplot as plt 


# ## Hyper Parameters

# In[2]:


msg_total = 8
channel = 4
epochs = 1000
batch_size = 1024
x=np.random.randint(0,8,10000)


# # Supervised Learning

# In[3]:


from keras.models import Sequential
from keras.layers import Dense, GaussianNoise
from keras.wrappers.scikit_learn import KerasClassifier

def func():
    model = Sequential()
    model.add(Dense(msg_total,input_dim=1,activation='relu'))
    model.add(Dense(2*channel, activation = 'linear'))
    model.add(GaussianNoise(1))
    model.add(Dense(msg_total, activation = 'softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam',metrics=['acc'])
    return model
  
estimator=KerasClassifier(build_fn=func,epochs=epochs,batch_size=batch_size,verbose=1)


# In[4]:


history=estimator.fit(x,x)
loss_supervised=history.history['loss']
acc=history.history['acc']


# In[5]:


x_test=np.random.randint(0,8,10)
print(x_test)
y_test=estimator.predict(x_test)
print(y_test)


# ## Alternate learning code

# In[6]:


import tensorflow as tf
from tensorflow import keras
from tensorflow import keras
from tensorflow.keras.layers import *
from sklearn import preprocessing
import tensorflow.keras.backend as K
from sklearn.metrics import mean_squared_error

sigma= 1e-4

# Peturbation Sampling
def perturbation(x):
    w = K.random_normal(shape = (channel,2), mean=0.0,stddev=sigma**0.5,dtype=None)
    xp = ((1-sigma)**0.5)*x + w
    return xp

# Defining transmitter loss
def loss_tx(y_true, y_pred):
    return -y_true*y_pred

# Defining the policy
def get_policy(inp):
    xp = inp[0]
    x = inp[1]
    w = xp - x
    policy = -K.sum(w*w)
    return policy


tx_inp = Input((1,))
# Adding embedding layer
embbedings_layer = Dense(msg_total, activation = 'relu')(tx_inp)
layer_dense = Dense(2*channel, activation = 'relu')(embbedings_layer)
# real to complex 
to_complex = Reshape((channel,2))(layer_dense)
# Normalising the output to unit energy
x = Lambda(lambda x: keras.backend.l2_normalize(x))(to_complex)
# Peturbation sampling 
xp = Lambda(perturbation)(to_complex)
policy = Lambda(get_policy)([xp,x])

# model for policy training
model_policy = keras.models.Model(inputs=tx_inp, outputs=policy)
# model to get the peturbatated output
model_tx = keras.models.Model(inputs=tx_inp, outputs=xp)
# model to get the encoded message to transmit
model_x = keras.models.Model(inputs=tx_inp, outputs=x)

model_policy.compile(loss=loss_tx, optimizer=tf.keras.optimizers.SGD(lr = 1e-5))
print(model_policy.summary())

rx_inp = Input((channel,2))
# complex to real
to_flat = Reshape((2*channel,))(rx_inp)
fc = Dense(8*2*channel, activation = 'relu')(to_flat)
softmax = Dense(msg_total, activation = 'softmax')(fc)

model_rx = keras.models.Model(inputs=rx_inp, outputs=softmax)

model_rx.compile(loss=tf.keras.losses.categorical_crossentropy, optimizer=tf.keras.optimizers.Adam())
print(model_rx.summary())

loss_tx = []
loss_rx = []
for epoch in range(epochs):
#     Transmitter Training
    raw_input = np.random.randint(0,msg_total,(batch_size))
    label = np.zeros((batch_size, msg_total))
    label[np.arange(batch_size), raw_input] = 1
    tx_input = raw_input/float(msg_total)
    xp = model_tx.predict(tx_input)
    y = xp + np.random.normal(0,0.001,(batch_size, channel,2))
    pred = model_rx.predict(y)
    loss = np.sum(np.square(label - pred), axis = 1)
    history_tx = model_policy.fit(tx_input, loss, batch_size=batch_size, epochs=1, verbose=0)    
    loss_tx.append(history_tx.history['loss'][0])
    
#     Receiver Training
    raw_input = np.random.randint(0,msg_total,(batch_size))
    label = np.zeros((batch_size, msg_total))
    label[np.arange(batch_size), raw_input] = 1
    tx_input = raw_input/float(msg_total)
    x = model_x.predict(tx_input)
    y = x + np.random.normal(0,0.001,(batch_size, channel,2))
    history_rx = model_rx.fit(y, label, batch_size=batch_size, epochs=1, verbose=0)
    loss_rx.append(history_rx.history['loss'][0])
    
    if(epoch % 100 == 0):
        print('epoch: ', epoch, 'tx_loss', history_tx.history['loss'][0], 'rx_loss', history_rx.history['loss'][0])


# # Comparision

# In[7]:


epoch_arr=range(1,epochs+1)
plt.title('Training error with epochs')
plt.plot(epoch_arr,loss_supervised,'r',label='Supervised training')
plt.plot(epoch_arr,loss_rx,'b',label='Alternating training')
plt.xlabel('epochs')
plt.ylabel('training error')
plt.legend()
plt.show()


# In[ ]:




