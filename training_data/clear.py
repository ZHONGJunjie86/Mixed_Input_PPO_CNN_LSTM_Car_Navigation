import numpy as np
import os
def reset():
    f=open(os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\training_data\\AC_critic_loss.csv', "r+")
    f.truncate()
    f=open(os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\training_data\\AC_reward.csv', "r+")
    f.truncate()
    f=open(os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\training_data\\AC_critic_3loss.csv', "r+")
    f.truncate()
    f=open(os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\training_data\\AC_3reward.csv', "r+")
    f.truncate()
    
    f=open(os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\training_data\\PPO_MC_critic_loss.csv', "r+")
    f.truncate()
    f=open(os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\training_data\\PPO_MC_reward.csv', "r+")
    f.truncate()
    f=open(os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\training_data\\PPO_TD_critic_loss.csv', "r+")
    f.truncate()
    f=open(os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\training_data\\PPO_TD_reward.csv', "r+")
    f.truncate()
    
reset()