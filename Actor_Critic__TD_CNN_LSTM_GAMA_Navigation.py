from utils import cross_loss_curve, GAMA_connect,reset,send_to_GAMA
from CV_input import generate_img
import os
from itertools import count
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import MultivariateNormal
import numpy as np
import pandas as pd

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 

save_curve_pic = os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\result\\Actor_Critic_loss_curve.png'
save_critic_loss = os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\training_data\\AC_critic_loss.csv'
save_reward = os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\training_data\\AC_reward.csv'
state_size = 6 
action_size = 1 
torch.set_default_tensor_type(torch.DoubleTensor)

class Actor(nn.Module):
    def __init__(self, state_size, action_size):
        super(Actor, self).__init__()
        self.conv1 = nn.Conv2d(3,8, kernel_size=8, stride=4, padding=0) # 500*500*3 -> 124*124*8
        self.maxp1 = nn.MaxPool2d(4, stride = 2, padding=0) # 124*124*8 -> 61*61*8
        self.conv2 = nn.Conv2d(8, 16, kernel_size=4, stride=1, padding=0) # 61*61*8 -> 58*58*16 
        self.maxp2 = nn.MaxPool2d(2, stride=2, padding=0) # 58*58*16  -> 29*29*16 = 13456
        self.linear_CNN = nn.Linear(13456, 256)
        #
        self.state_size = state_size
        self.action_size = action_size
        self.linear1 = nn.Linear(self.state_size, 32)
        self.linear2 = nn.Linear(32, 32)
        
        self.LSTM_layer_3 = nn.LSTM(288,64,1, batch_first=True)
        self.linear4 = nn.Linear(64,32)
        self.mu = nn.Linear(32,self.action_size)  #256 linear2
        self.sigma = nn.Linear(32,self.action_size)
        self.hidden_cell = (torch.zeros(1,1,64).to(device),
                            torch.zeros(1,1,64).to(device))

    def forward(self, state,tensor_cv):
        # CV
        x = F.relu(self.maxp1(self.conv1(tensor_cv.unsqueeze(0))))
        x = F.relu(self.maxp2(self.conv2(x)))
        x = x.view(x.size(0), -1) #展開
        x = F.relu(self.linear_CNN(x))
        # num
        output_1 = F.relu(self.linear1(state))
        output_2 = F.relu(self.linear2(output_1))
        # LSTM
        output_2 = torch.cat((x,output_2),1) 
        output_2  = output_2.unsqueeze(0)
        output_3 , self.hidden_cell = self.LSTM_layer_3(output_2) #,self.hidden_cell
        a,b,c = output_3.shape
        #
        output_4 = F.relu(self.linear4(output_3.view(-1,c))) #
        mu =  torch.tanh(self.mu(output_4))   #有正有负 sigmoid 0-1
        sigma = F.relu(self.sigma(output_4)) + 0.001 
        mu = torch.diag_embed(mu).to(device)
        sigma = torch.diag_embed(sigma).to(device)  # change to 2D
        dist = MultivariateNormal(mu,sigma)  #N(μ，σ^2)
        entropy = dist.entropy().mean()
        action = dist.sample()
        action_logprob = dist.log_prob(action)     
        return action,action_logprob,entropy

class Critic(nn.Module):
    def __init__(self, state_size, action_size):
        super(Critic, self).__init__()
        self.conv1 = nn.Conv2d(3,8, kernel_size=8, stride=4, padding=0) # 500*500*3 -> 124*124*8
        self.maxp1 = nn.MaxPool2d(4, stride = 2, padding=0) # 124*124*8 -> 61*61*8
        self.conv2 = nn.Conv2d(8, 16, kernel_size=4, stride=1, padding=0) # 61*61*8 -> 58*58*16 
        self.maxp2 = nn.MaxPool2d(2, stride=2, padding=0) # 58*58*16  -> 29*29*16 = 13456
        self.linear_CNN = nn.Linear(13456, 256)
        #
        self.state_size = state_size
        self.action_size = action_size
        self.linear1 = nn.Linear(self.state_size, 32)
        self.linear2 = nn.Linear(32, 32)
        self.LSTM_layer_3 = nn.LSTM(288,64,1, batch_first=True)
        self.linear4 = nn.Linear(64,32) #
        self.linear5 = nn.Linear(32, action_size)
        self.hidden_cell = (torch.zeros(1,1,64).to(device),
                            torch.zeros(1,1,64).to(device))

    def forward(self, state, tensor_cv):
        #CV
        x = F.relu(self.maxp1(self.conv1(tensor_cv.unsqueeze(0))))
        x = F.relu(self.maxp2(self.conv2(x)))
        x = x.view(x.size(0), -1)
        x = F.relu(self.linear_CNN(x))
        #num
        output_1 = F.relu(self.linear1(state))
        output_2 = F.relu(self.linear2(output_1))
        #LSTM
        output_2 = torch.cat((x,output_2),1)
        output_2  = output_2.unsqueeze(0)
        output_3 , self.hidden_cell = self.LSTM_layer_3(output_2) #,self.hidden_cell
        a,b,c = output_3.shape
        #
        output_4 = F.relu(self.linear4(output_3.view(-1,c))) 
        value  = torch.tanh(self.linear5(output_4))
        return value #,output

def main():
    ################ load ###################
    actor_path = os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\weight\\AC_TD_actor.pkl'
    critic_path = os.path.abspath(os.curdir)+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\weight\\AC_TD_critic.pkl'
    if os.path.exists(actor_path):
        actor =  Actor(state_size, action_size).to(device)
        actor.load_state_dict(torch.load(actor_path))
        print('Actor Model loaded')
    else:
        actor = Actor(state_size, action_size).to(device)
    if os.path.exists(critic_path):
        critic = Critic(state_size, action_size).to(device)
        critic.load_state_dict(torch.load(critic_path))
        print('Critic Model loaded')
    else:
        critic = Critic(state_size, action_size).to(device)
    critic_next = Critic(state_size, action_size).to(device)
    critic_next.load_state_dict(critic.state_dict())
    print("Waiting for GAMA...")
    ################### initialization ########################
    reset()

    episode = 237

    lr = 0.0001
    if episode > 50 :
        lr = 0.00008
        new_lr = lr * (0.9 ** ((episode-40) // 10))
        #if episode > 110:
         #   lr = 0.000008
          #  new_lr = lr * (0.9 ** ((episode-90) // 10)) #40

    optimizerA = optim.Adam(actor.parameters(), lr, betas=(0.95, 0.999))
    optimizerC = optim.Adam(critic.parameters(), lr, betas=(0.95, 0.999))

    test = "GAMA"
    state,reward,done,time_pass,over = GAMA_connect(test) #connect
    print("done:",done,"timepass:",time_pass)
    log_probs = [] #log probability
    values = []
    rewards = []
    masks = []
    total_loss = []
    total_rewards = []
    entropy = 0
    loss = []
    value = 0
    log_prob = 0
    gama = 0.9
    C_cx = torch.zeros(64).reshape(1,1,64).to(device)
    lstm_output_c = 0
    lstm_output_a = 0

    ##################  start  #########################
    while over!= 1:
        #普通の場合
        if(done == 0 and time_pass != 0):  
            #前回の報酬
            reward = torch.tensor([reward], dtype=torch.float, device=device)
            rewards.append(reward)   
            state_next = torch.DoubleTensor(state).reshape(1,6).to(device)
            state_img = generate_img() 
            tensor_cv = torch.from_numpy(np.transpose(state_img, (2, 0, 1))).double().to(device)
            value_next = critic_next(state_next,tensor_cv) 
            
            with torch.autograd.set_detect_anomaly(True):
                # TD:r(s) +  gama*v(s+1) - v(s)
                advantage = reward.detach() + gama*value_next.detach() - value 
                actor_loss = -(log_prob * advantage.detach())     
                critic_loss = (reward.detach() + gama*value_next.detach() - value).pow(2) 
                optimizerA.zero_grad()
                optimizerC.zero_grad()
                critic_loss.backward()  
                actor_loss.backward()
                loss.append(critic_loss)
                optimizerA.step()
                optimizerC.step()
                critic_next.load_state_dict(critic.state_dict())

            state = torch.DoubleTensor(state).reshape(1,6).to(device)
            value =  critic(state,tensor_cv)  
            action,log_prob,entropy = actor(state,tensor_cv) 
            log_prob = log_prob.unsqueeze(0)           
            entropy += entropy

            send_to_GAMA([[1,float(action.cpu().numpy()*10)]]) #行
            masks.append(torch.tensor([1-done], dtype=torch.float, device=device))  
            values.append(value)
            log_probs.append(log_prob)

        # 終わり 
        elif done == 1:
            #print("restart acceleration: 0")
            send_to_GAMA([[1,0]])
            #先传后计算
            print(state)
            rewards.append(reward) #contains the last
            reward = torch.tensor([reward], dtype=torch.float, device=device)
            rewards.append(reward) #contains the last
            total_reward = sum(rewards).cpu().detach().numpy()
            total_rewards.append(total_reward)
            
            #state = torch.FloatTensor(state).reshape(1,4).to(device)
            #last_value= critic(state)

            with torch.autograd.set_detect_anomaly(True):
                advantage = reward.detach() - value            #+ last_value   最后一回的V(s+1) = 0
                actor_loss = -( log_prob * advantage.detach())    
                critic_loss = (reward.detach()  - value).pow(2)  #+ last_value
                lstm_loss = critic_loss

                optimizerA.zero_grad()
                optimizerC.zero_grad()

                critic_loss.backward() 
                actor_loss.backward()
                loss.append(critic_loss)
                
                optimizerA.step()
                optimizerC.step()

                critic_next.load_state_dict(critic.state_dict())

            print("----------------------------------Net_Trained---------------------------------------")
            print('--------------------------Iteration:',episode,'over--------------------------------')
            episode += 1
            log_probs = []
            values = []
            rewards = []
            masks = [] 
            loss_sum = sum(loss).cpu().detach().numpy()
            total_loss.append(loss_sum)
            cross_loss_curve(loss_sum.squeeze(0),total_reward,save_curve_pic,save_critic_loss,save_reward) #total_loss,total_rewards
            loss = []
            if episode > 50 :
                lr = 0.00008
                new_lr = lr * (0.9 ** ((episode-40) // 10))
                #if episode > 110:
                 #   lr = 0.000008
                  #  new_lr = lr * (0.9 ** ((episode-90) // 10)) #40
                optimizerA = optim.Adam(actor.parameters(), new_lr, betas=(0.95, 0.999))
                optimizerC = optim.Adam(critic.parameters(), new_lr, betas=(0.95, 0.999))

            torch.save(actor.state_dict(),actor_path)
            torch.save(critic.state_dict(),critic_path)

        #最初の時
        else:
            print('Iteration:',episode)
            state = np.reshape(state,(1,len(state))) #xxx
            state_img = generate_img() 
            tensor_cv = torch.from_numpy(np.transpose(state_img, (2, 0, 1))).double().to(device)
            state = torch.DoubleTensor(state).reshape(1,6).to(device)
            value =  critic(state,tensor_cv)  #dist,  # now is a tensoraction = dist.sample() 
            action,log_prob,entropy = actor(state,tensor_cv)
            print("acceleration: ",action.cpu().numpy())
            send_to_GAMA([[1,float(action.cpu().numpy()*10)]])
            log_prob = log_prob.unsqueeze(0)
            entropy += entropy

        state,reward,done,time_pass,over = GAMA_connect(test)
    return None 

if __name__ == '__main__':
    main()
