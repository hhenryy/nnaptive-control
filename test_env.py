#!/usr/bin/env python3
import numpy as np
import sys
import argparse
import tensorflow as tf
from second_order import second_order
from single_pendulum_v2 import pendulum
from linear_control import PIDcontroller
import os
import pickle
import shelve
from tensorflow import keras
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser(\
        prog='Test the performance of neural network',\
        description='Environment where the trained neural network is tested'
        )


parser.add_argument('-loc', default='./train_data/', help='location to store responses, default: ./train_data')
parser.add_argument('-init', default=4, help='offset from working point')
parser.add_argument('-wp', default=0, help='working point')
parser.add_argument('-model_path', default='./nn_mdl', help='path to neural network model')


args = parser.parse_args()

model_path = vars(args)['model_path']

dir = vars(args)['loc']

# Working point
wp = float(vars(args)['wp'])
# initial conditions of pendulum
theta = wp + float(vars(args)['init'])




print('----------------------------------------------------------------')
print('Fetching training info from: ', str(dir+'/readme'))
print('----------------------------------------------------------------')
with shelve.open( str(dir+'/readme')) as db:
    zeta=float((db)['zeta'])
    wn=float((db)['wn'])
    sim_time = int((db)['t'])
    dt = float((db)['dt'])
    N = 5

db.close()


print('----------------------------------------------------------------')
print('Simulation Information: ')
print('----------------------------------------------------------------')
with shelve.open(str(dir+'/readme')) as db:
    for key,value in db.items():
        print("{}: {}".format(key, value))
db.close()
print('wp: ',wp)
print('theta: ', theta)
print('----------------------------------------------------------------')



print('------------------------------------------------------------------------------------------------------')
print('Fetching neural network model from: ', str(model_path ))
print('------------------------------------------------------------------------------------------------------')

nn_model = keras.models.load_model(str(model_path))

inputsize = nn_model.get_input_shape_at(0)

# input to neural network

nn_input_matrix = np.zeros((1,2*N)).astype(np.float32)

# Conversion to radians
deg2rad = np.pi/180

wp = wp*deg2rad
theta = theta*deg2rad


# constant
t = 0


error = 0
ref =   10 * deg2rad

if __name__ == '__main__':


    # Size for arrays
    total_steps = int(np.ceil(sim_time/dt))
    t = 0
    # counter
    step = 0

    # y generated by nonlinear model
    y_hat = np.zeros(total_steps)

    # y generated by linear model
    y_star = np.zeros(total_steps)

    # Error between y_hat and y_star
    e = np.zeros(total_steps)

    # Control generated by linear controller
    u_star = np.zeros(total_steps)

    # control received by nonlinear model
    u_hat = np.zeros(total_steps)

    # Generated neural network control output
    u_nn = np.zeros(total_steps)

    # Error between reference and y_hat
    error = np.zeros(total_steps)


    # Pendulum linearised around unstable inverted position
    linearised_model = second_order(wn=wn,zeta=zeta,time_step=dt,y=theta,y_wp=wp)

    # Nonlinear model of the pendulum
    pendulums = pendulum(wn=wn,zeta=zeta,time_step=dt,y=theta)
    # pendulums = second_order(wn=wn,zeta=zeta,time_step=dt,y=theta,y_wp=wp)

    # Linear PID Controller
    linear_controller = PIDcontroller(P,I,D,dt=dt)




    while t < sim_time-dt/2:

        # output of nonlinear model
        y_hat[step] = pendulums.getAllStates()[3]
        # output of the linear model
        y_star[step] = linearised_model.getAllStates()[3]

        # Error between the outputs of the linearised and nonlinead model
        e[step] = y_hat[step] - y_star[step]

        # Define the initial error
        error[step] = ref - y_hat[step]

        linear_controller.step(error[step])
        control_output = linear_controller.outputControl()
        # Determine where the linear controller will take the linearised model
        linearised_model.update_input(control_output)
        y_ref = linearised_model.step().getAllStates()[3]

        # linear controller output
        u_star[step] = control_output

        nn_input_matrix = np.roll(nn_input_matrix,-1) # move elements one timestep back

        # insert new timestep
        nn_input_matrix[0,N-1] = y_hat[step]
        nn_input_matrix[0,2*N-1] = u_hat[step-1]

        # reshape
        nn_input = np.array(nn_input_matrix.reshape((1,10)))
        # print(nn_input)
        u_nn[step] = nn_model.predict(nn_input)

        u_hat[step] = u_nn[step]


        pendulums.update_input(u_hat[step])
        pendulums.step()


        # Increment time
        t += dt
        # Increment counter
        step += 1



plt.rc('text', usetex=True)
plt.rc('font', family='serif')
plt.rc('font', size=12)

plt.figure(1)
plt.plot(y_star,'-', mew=1, ms=8,mec='w')
plt.plot(y_hat,'-', mew=1, ms=8,mec='w')
plt.grid()
plt.legend(['$y^{*}$','$\hat y$'])

plt.figure(2)
plt.plot(e,'-', mew=1, ms=8,mec='w')
plt.grid()
plt.title('$y^{*}-\hat y$')

plt.figure(3)
plt.plot(error,'-', mew=1, ms=8,mec='w')
plt.grid()
plt.title('Error signal')


plt.figure(4)
# plt.plot(u_nn,'-', mew=1, ms=8,mec='w')
plt.plot(u_hat,'-', mew=1, ms=8,mec='w')
plt.plot(u_star,'-', mew=1, ms=8,mec='w')
plt.plot(u_nn,'-', mew=1, ms=8,mec='w')
plt.grid()
plt.legend(['$\hat u$','$u^{*}$','$u_{NN}$'])


plt.figure(5)
plt.plot(u_nn,'-', mew=1, ms=8,mec='w')
plt.grid()
plt.title('Neural Network Output')


plt.figure(6)
plt.plot(u_nn,'-', mew=1, ms=8,mec='w')
plt.plot(e,'-', mew=1, ms=8,mec='w')
plt.grid()
plt.legend(['$u_{NN}$','$y^{*}-\hat y$'])



plt.figure(7)
plt.plot(u_nn,'-', mew=1, ms=8,mec='w')
plt.plot(u_star,'-', mew=1, ms=8,mec='w')
plt.grid()
plt.legend(['$u_{NN}$','$u^{*}$'])


plt.show()
