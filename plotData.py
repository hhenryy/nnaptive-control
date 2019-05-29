#!/usr/bin/env python3
# from uav_model import drone
import numpy as np
import matplotlib.pyplot as plt
import sys
import argparse


parser = argparse.ArgumentParser(\
        prog='Plot Data',\
        description='Creates .npz files of step responses with given damping ratio\
                    frequency'
        )


parser.add_argument('-loc', default='./train_data/', help='location to store responses, default: ./train_data')
parser.add_argument('-filename', default="response-0.npz", help='filename, default: response-0.npz')
parser.add_argument('-n', default=0, help='plot a specific number response')
parser.add_argument('-dot', default=0, help='plot a with dotted line')
parser.add_argument('-biased', default=0, help='add biased plot')


args = parser.parse_args()

dir = vars(args)['loc']
filename = vars(args)['loc']+'/'+vars(args)['filename']
number = int(vars(args)['n'])
dot = int(vars(args)['dot'])
biased = int(vars(args)['biased'])

filename = filename.replace(str(0),str(number))
print("Plotting Response of file: ", filename)


data = np.load(filename)

y = data['y_']
ydot = data['y_dot']
ydotdot = data['y_dotdot']
input = data['input']
bias = data['bias']

if(biased):
    biased_y = data['biased_y']
    biased_ydot = data['biased_y_dot']
    biased_ydotdot = data['biased_y_dotdot']

plt.rc('text', usetex=True)
plt.rc('font', family='serif')
plt.rc('font', size=12)

if(not dot):
    plt.figure(1)
    plt.plot(input,'-', mew=1, ms=8,mec='w')
    plt.plot(ydotdot,'-', mew=1, ms=8,mec='w')
    plt.plot(ydot,'-', mew=1, ms=8,mec='w')
    plt.plot(y,'-', mew=1, ms=8,mec='w')
    plt.plot(bias,'-', mew=1, ms=8,mec='w')
    plt.legend(['$input$','$\ddot y$','$\dot y $','$y$','bias'])
    plt.grid()


else:
    plt.figure(1)
    plt.plot(input,'.-', mew=1, ms=8,mec='w')
    plt.plot(ydotdot,'.-', mew=1, ms=8,mec='w')
    plt.plot(ydot,'.-', mew=1, ms=8,mec='w')
    plt.plot(y,'.-', mew=1, ms=8,mec='w')
    plt.legend(['$input$','$\ddot y$','$\dot y $','$y$'])
    plt.grid()

if(biased):
    plt.figure(2)
    plt.plot(y,'-', mew=1, ms=8,mec='w')
    plt.plot(biased_y,'-', mew=1, ms=8,mec='w')
    plt.plot(bias,'-', mew=1, ms=8,mec='w')
    plt.legend(['$y$','$biased y$','biased',])
    plt.grid()



plt.show()


data.close()
