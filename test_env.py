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
from scipy.optimize import curve_fit

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
print('Training Information: ')
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
N=10
nn_input_matrix = np.zeros((1,2*N))

# Conversion to radians
deg2rad = np.pi/180

wp = wp*deg2rad
theta = 0*deg2rad


# constant
t = 0



def generateStepInput(responseDuration,startInput,minInput,maxInput):

    input = np.zeros( (responseDuration,1) )
    timestep = startInput

    while timestep < responseDuration:
        magInput = (maxInput-minInput)*np.random.random()+minInput # Magnitude Size of Input
        inputDur = int(responseDuration/10*(np.random.random() ) ) # Duration of input
        zeroInputDur = int(responseDuration/10*(np.random.random()) ) # Duration of zero input


        input[timestep:timestep+inputDur] = magInput
        timestep += inputDur
        input[timestep:timestep+zeroInputDur] = 0
        timestep += zeroInputDur

    return input



def generateRampInput(responseDuration,startInput,minInput,maxInput):

    input = np.zeros( (responseDuration,1) )
    timestep = startInput

    while timestep < responseDuration:
        magInput = (maxInput-minInput)*np.random.random()+minInput # peak point in ramp
        firstDur = int(responseDuration/10*(np.random.random() ) )+1 # Duration of first half ramp
        secondDur = int(responseDuration/10*(np.random.random()) )+1 # Duration of second half ramp
        if(timestep + firstDur+secondDur < responseDuration):

            grad1 = magInput/firstDur   # gradient of first part
            grad2 = -magInput/secondDur  # Gradientr of second part

            firstLine = np.arange(firstDur)*grad1

            secondLine = -1*np.arange(secondDur,0,-1)*grad2
            input[timestep:timestep+firstDur] = np.transpose(np.array([firstLine]))
            timestep += firstDur
            input[timestep:timestep+secondDur] = np.transpose(np.array([secondLine]))
            timestep += secondDur
        else:
            break

    return input

def straightline_func(x, a, b):
    return a*x+b

def exponential_func(x, a, b):
    return a*np.exp(b*x)

def quadratic_func(x,a):
    return a*np.power(x,2)

def generateAccInput(responseDuration,startInput,minInput,maxInput):
    input = np.zeros( (responseDuration,1) )
    timestep = startInput

    while timestep < responseDuration:

        magInput = (maxInput-minInput)*np.random.random()+minInput # peak point in ramp
        Dur = int(responseDuration/10*(np.random.random()))+10 # Duration of first half ramp
        Dur2 = int(responseDuration/10*(np.random.random()))+10 # Duration of first half ramp
        neg = 1.0

        if(magInput < 0):
            magInput = -1*magInput
            neg = -1.0

        if(timestep + Dur + Dur2+1 < responseDuration):
            y_ = np.sqrt(np.array([0.00001, magInput]))
            x = np.array([timestep+1,timestep+Dur])
            popt, pcov = curve_fit(straightline_func, x, y_)
            a = np.power(popt[0],2)

            curve = np.arange(timestep,timestep+Dur)
            curve = neg*quadratic_func(curve, a)

            input[timestep:timestep+Dur] = np.transpose(np.array([curve]))

            y_ = np.sqrt(np.array([magInput, 0.001]))
            x = np.array([timestep+Dur,timestep+Dur+Dur2])
            popt, pcov = curve_fit(straightline_func, x, y_)
            a = popt[0]
            curve = np.arange(timestep+Dur,timestep+Dur+Dur2)
            curve = neg*quadratic_func(curve, a)
            input[timestep+Dur:timestep+Dur+Dur2] = np.transpose(np.array([curve]))


            timestep = timestep + Dur+Dur2
        else:
            break

    return input

def generateExpoInput(responseDuration,startInput,minInput,maxInput):
    input = np.zeros( (responseDuration,1) )
    timestep = startInput

    while timestep < responseDuration:

        magInput = (maxInput-minInput)*np.random.random()+minInput # peak point in ramp
        Dur = int(responseDuration/10*(np.random.random()))+10 # Duration of first half ramp
        Dur2 = int(responseDuration/10*(np.random.random()))+10 # Duration of first half ramp
        neg = 1.0

        if(magInput < 0):
            magInput = -1*magInput
            neg = -1.0

        if(timestep + Dur + Dur2+1 < responseDuration):
            y_ = np.log(np.array([0.001, magInput]))
            x = np.array([timestep+1,timestep+Dur])
            popt, pcov = curve_fit(straightline_func, x, y_)
            b = popt[0]
            a = np.exp(popt[1])

            curve = np.arange(timestep,timestep+Dur)
            curve = neg*exponential_func(curve, a, b)

            input[timestep:timestep+Dur] = np.transpose(np.array([curve]))

            y_ = np.log(np.array([magInput, 0.001]))
            x = np.array([timestep+Dur,timestep+Dur+Dur2])
            popt, pcov = curve_fit(straightline_func, x, y_)
            b = popt[0]
            a = np.exp(popt[1])
            curve = np.arange(timestep+Dur,timestep+Dur+Dur2)
            curve = neg*exponential_func(curve, a, b)
            input[timestep+Dur:timestep+Dur+Dur2] = np.transpose(np.array([curve]))


            timestep = timestep + Dur+Dur2
        else:
            break

    return input

def generateNoiseInput(responseDuration,startInput,minInput,maxInput):

    input = np.zeros( (responseDuration,1) )
    input += (maxInput-minInput)*np.random.random((np.size(input),1))+minInput
    return input

def addNoise(response,level):
    sizeOfArray = np.size(response)
    response += np.random.random((sizeOfArray,1))/level
    return response

def generateCombinationInput(responseDuration,startInput,minInput,maxInput):
    input1 = generateStepInput(responseDuration,startInput,minInput/3,maxInput/3)
    input2 = generateRampInput(responseDuration,startInput,minInput/3,maxInput/3)
    input3 = generateExpoInput(responseDuration,startInput,minInput/3,maxInput/3)
    input = addNoise(input1+input2+input3,250)
    return input


error = 0
ref =   20 * deg2rad

if __name__ == '__main__':


    # Size for arrays
    total_steps = int(np.ceil(t/dt))
    # from other branch, will need to be change
    dt = 0.01
    total_steps = 1000
    # sim_time = t
    #

    t = 0
    # counter
    step = 0

    # Creat Input

    fake_control = generateCombinationInput(total_steps,50,-0.5,0.5)

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
    P=0.5
    I=0.5
    D=0
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
        control_output = fake_control[step]

        # Determine where the linear controller will take the linearised model
        pendulums.update_input(control_output)
        pendulums.step()
        y_ref = pendulums.getAllStates()[3]

        # linear controller output
        u_star[step] = control_output

        nn_input_matrix = np.roll(nn_input_matrix,1) # move elements one timestep back

        # insert new timestep
        nn_input_matrix[0,0] = u_star[step-1]
        nn_input_matrix[0,N] = y_ref
        # reshape
        # print(nn_input_matrix)
        nn_input = nn_input_matrix[0].reshape((1,20))
        # print(nn_input)
        u_nn[step] = nn_model.predict(nn_input)
        # print(u_nn[step])
        u_hat[step] = u_nn[step]


        # pendulums.update_input(u_nn[step])
        # # pendulums.update_input(u_star[step])
        # pendulums.step()


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
plt.plot(fake_control,'-', mew=1, ms=8,mec='w')
plt.plot(u_star,'-', mew=1, ms=8,mec='w')
plt.grid()
plt.legend(['$u_{NN}$','$u^{*}$'])


plt.show()
