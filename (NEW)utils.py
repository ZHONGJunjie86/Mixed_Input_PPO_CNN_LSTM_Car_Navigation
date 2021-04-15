import matplotlib.pyplot as plt
import numpy as np
import time,random
import os 

from_GAMA_1 = os.getcwd()+'/PPO_Mixedinput_Navigation_Model/GAMA_R/GAMA_intersection_data_1.csv'
from_GAMA_2 = os.getcwd()+'/PPO_Mixedinput_Navigation_Model/GAMA_R/GAMA_intersection_data_2.csv'
from_python_1 = os.getcwd()+'/PPO_Mixedinput_Navigation_Model/GAMA_R/python_AC_1.csv'
from_python_2 = os.getcwd()+'/PPO_Mixedinput_Navigation_Model/GAMA_R/python_AC_2.csv'
save_curve_pic_speed = save_curve_pic = os.path.abspath(os.curdir)+'/PPO_Mixedinput_Navigation_Model/result/Actor_Critic_3_average_speed.png'

def reset():
    f=open(from_GAMA_1, "r+")
    f.truncate()
    f=open(from_GAMA_2, "r+")
    f.truncate()
    f=open(from_python_1, "r+")
    f.truncate()
    f=open(from_python_2, "r+")
    f.truncate()
    return_ = [0]
    np.savetxt(from_python_1,return_,delimiter=',')
    np.savetxt(from_python_2,return_,delimiter=',')

def cross_loss_curve(critic_loss,total_rewards,save_curve_pic,save_critic_loss,save_reward,average_speed,save_speed,average_speed_NPC,save_NPC_speed):
    critic_loss = np.hstack((np.loadtxt(save_critic_loss, delimiter=","),critic_loss))
    reward = np.hstack((np.loadtxt(save_reward, delimiter=",") ,total_rewards))
    average_speeds = np.hstack((np.loadtxt(save_speed, delimiter=",") ,average_speed))
    NPC_speeds = np.hstack((np.loadtxt(save_NPC_speed, delimiter=",") ,average_speed_NPC))
    plt.plot(np.array(critic_loss), c='b', label='critic_loss', linewidth=0.4)
    plt.plot(np.array(reward), c='r', label='total_rewards', linewidth=0.4)
    plt.legend(loc='best')
    #plt.ylim(-15,15)
    plt.ylim(-0.25,0.05)
    plt.ylabel('critic_loss') 
    plt.xlabel('training steps')
    plt.grid()
    plt.savefig(save_curve_pic)
    plt.close()
    #
    plt.plot(np.array(NPC_speeds), c='b', label='NPC_average_speeds m/s',linewidth=0.5)
    plt.plot(np.array(average_speeds), c='g', label='RL_average_speeds m/s',linewidth=0.5)
    plt.legend(loc='best')
    plt.ylabel('average_speed m/s') 
    plt.xlabel('training steps')
    plt.grid()
    plt.savefig(save_curve_pic_speed)
    plt.close()
    #
    np.savetxt(save_critic_loss,critic_loss,delimiter=',')
    np.savetxt(save_reward,reward,delimiter=',')
    np.savetxt(save_speed,average_speeds,delimiter=',')
    np.savetxt(save_NPC_speed,NPC_speeds,delimiter=',')

def send_to_GAMA(to_GAMA):
    error = True
    while error == True:
        try:
            np.savetxt(from_python_1,to_GAMA,delimiter=',')
            np.savetxt(from_python_2,to_GAMA,delimiter=',')
            error = False
        except(IndexError,FileNotFoundError,ValueError,OSError,PermissionError):  
            error = True 

#[real_speed/10, target_speed/10, elapsed_time_ratio, distance_left/100,distance_front_car/10,distance_behind_car/10,reward,done,over]
def GAMA_connect(test):
    error = True
    while error == True:
        try:
            time.sleep(0.003)
            if(random.random()>0.3):
                state = np.loadtxt(from_GAMA_1, delimiter=",")
            else:
                state = np.loadtxt(from_GAMA_2, delimiter=",")
            time_pass = state[2]
            error = False
        except (IndexError,FileNotFoundError,ValueError,OSError):
            time.sleep(0.003)
            error = True
        
    reward = state[6]
    done = state[7]  # time_pass = state[6]
    over = state [8] 
    average_speed_NPC =state[9]
    #print("Recived:",state," done:",done)
    state = np.delete(state, [2,3,5,6,7,8,9], axis = 0) #4,5,  # 3!!!!
    error = True
    while error == True:
        try:
            f1=open(from_GAMA_1, "r+")
            f1.truncate()
            f2=open(from_GAMA_2, "r+")
            f2.truncate()
            error = False
        except (IndexError,FileNotFoundError,ValueError,OSError):
            time.sleep(0.003)
            error = True

    return state,reward,done,time_pass,over,average_speed_NPC