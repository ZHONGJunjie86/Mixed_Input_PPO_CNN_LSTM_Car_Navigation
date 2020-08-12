from utils import cross_loss_curve, GAMA_connect,send_to_GAMA,reset
from CV_input import generate_img
import os
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import MultivariateNormal
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings("ignore")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu") #
torch.set_default_tensor_type(torch.DoubleTensor)

class Memory:
    def __init__(self):
        self.actions = []
        self.states = []
        self.states_next = []
        self.states_img = []
        self.states_img_next = []
        self.logprobs = []
        self.rewards = []
        self.is_terminals = []
    
    def clear_memory(self):
        del self.actions[:]
        del self.states[:]
        del self.states_next[:]
        del self.states_img[:]
        del self.states_img_next[:]
        del self.logprobs[:]
        del self.rewards[:]
        del self.is_terminals[:]

class Actor(nn.Module):
    def __init__(self, state_size, action_size):
        super(Actor, self).__init__()
        self.conv1 = nn.Conv2d(3,8, kernel_size=8, stride=4, padding=0) # 500*500*3 -> 124*124*8
        self.maxp1 = nn.MaxPool2d(4, stride = 2, padding=0) # 124*124*8 -> 61*61*8
        self.conv2 = nn.Conv2d(8, 16, kernel_size=4, stride=1, padding=0) # 61*61*8 -> 58*58*16 
        self.maxp2 = nn.MaxPool2d(2, stride=2, padding=0) # 58*58*16  -> 29*29*16 = 13456
        self.linear_CNN = nn.Linear(13456, 256)   # *3
        self.lstm_CNN = nn.LSTM(768,256)
        
        #
        self.state_size = state_size
        self.action_size = action_size
        self.linear1 = nn.Linear(self.state_size, 128)
        self.linear2 = nn.Linear(128,128)
        self.lstm3 = nn.LSTM(128,85)
        
        self.LSTM_layer_3 = nn.LSTM(511,128,1, batch_first=True)
        self.linear4 = nn.Linear(128,32)
        self.mu = nn.Linear(32,self.action_size)  #256 linear2
        self.sigma = nn.Linear(32,self.action_size)
        self.hidden_cell = (torch.zeros(1,1,64).to(device),
                            torch.zeros(1,1,64).to(device))

    def forward(self, state,tensor_cv):
        # CV
        x = F.relu(self.maxp1(self.conv1(tensor_cv)))
        x = F.relu(self.maxp2(self.conv2(x)))
        x = x.view(x.size(0), -1) #展開
        x = F.relu(self.linear_CNN(x)).reshape(1,768)
        x,_ = self.lstm_CNN(x.unsqueeze(0))
        x = F.relu( x).reshape(1,256)  #torch.tanh
        
        # num
        output_1 = F.relu(self.linear1(state))
        output_2 = F.relu(self.linear2(output_1))
        output_2,_ = self.lstm3(output_2)
        output_2 = F.relu(output_2)  #
        output_2 = output_2.squeeze().reshape(1,255)
        # LSTM
        output_2 = torch.cat((x,output_2),1) 
        output_2  = output_2.unsqueeze(0)
        output_3 , self.hidden_cell = self.LSTM_layer_3(output_2) #,self.hidden_cell
        a,b,c = output_3.shape
        #
        output_4 = F.relu(self.linear4(output_3.view(-1,c))) #
        mu = torch.tanh(self.mu(output_4))   #有正有负 sigmoid 0-1
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
        self.lstm_CNN = nn.LSTM(768,256)
        #
        self.state_size = state_size
        self.action_size = action_size
        self.linear1 = nn.Linear(self.state_size, 128)
        self.linear2 = nn.Linear(128, 128)
        self.lstm3 = nn.LSTM(128,85)
        #
        self.LSTM_layer_3 = nn.LSTM(511,128,1, batch_first=True)
        self.linear4 = nn.Linear(128,32) #
        self.linear5 = nn.Linear(32, action_size)
        self.hidden_cell = (torch.zeros(1,1,64).to(device),
                            torch.zeros(1,1,64).to(device))

    def forward(self, state, tensor_cv):
        #CV
        x = F.relu(self.maxp1(self.conv1(tensor_cv)))
        x = F.relu(self.maxp2(self.conv2(x)))
        x = x.view(x.size(0), -1)
        x = F.relu(self.linear_CNN(x)).reshape(1,768)
        x,_ = self.lstm_CNN(x.unsqueeze(0))
        x = F.relu( x).reshape(1,256)
        #num
        output_1 = F.relu(self.linear1(state))
        output_2 = F.relu(self.linear2(output_1))
        output_2,_ = self.lstm3(output_2)
        output_2 = F.relu(output_2)
        output_2 = output_2.squeeze().reshape(1,255)
        #LSTM
        output_2 = torch.cat((x,output_2),1)
        output_2  = output_2.unsqueeze(0)
        output_3 , self.hidden_cell = self.LSTM_layer_3(output_2) #,self.hidden_cell
        a,b,c = output_3.shape
        #
        output_4 = F.relu(self.linear4(output_3.view(-1,c))) 
        value  = torch.tanh(self.linear5(output_4))
        return value #,output

class PPO:
    def __init__(self, state_dim, action_dim, lr,gamma, K_epochs, eps_clip):
        self.lr = lr
        self.gamma = gamma
        self.eps_clip = eps_clip
        self.K_epochs = K_epochs
        self.memory_size = 3
        self.memory_counter = 0
        
        self.actor = Actor(state_dim, action_dim).to(device)
        self.critic = Critic(state_dim, action_dim).to(device)
        self.critic_next = Critic(state_dim, action_dim).to(device)
        self.critic_next.load_state_dict(self.critic.state_dict())
        self.A_optimizer = torch.optim.Adam(self.actor.parameters(), lr=lr, betas=(0.95, 0.999)) #更新新网
        self.C_optimizer = torch.optim.Adam(self.critic.parameters(), lr=lr, betas=(0.95, 0.999)) #更新新网

        self.MseLoss = nn.MSELoss()
    
    def select_action(self, state, tensor_cv,memory):
        if  len(memory.states)==0:
            for _ in range(3):
                memory.states.append(state)
                memory.states_img.append(tensor_cv)
        else:
            del memory.states[:1]
            del memory.states_img[:1]
            memory.states.append(state)
            memory.states_img.append(tensor_cv)
        state = torch.stack(memory.states,0)
        tensor_cv = torch.stack(memory.states_img,0)
        action,action_logprob,entropy = self.actor(state,tensor_cv)
        memory.actions.append(action)
        memory.logprobs.append(action_logprob)
        action.detach()
        action = torch.clamp(action, -0.6, 0.6) #limit
        return action.cpu().data.numpy().flatten()
    
    def update(self, memory,lr,advantages,done):
        # 更新lr
        self.A_optimizer = torch.optim.Adam(self.actor.parameters(), lr=lr, betas=(0.95, 0.999)) #更新新网
        self.C_optimizer = torch.optim.Adam(self.critic.parameters(), lr=lr, betas=(0.95, 0.999)) #更新新网
        # Monte Carlo estimate of rewards: MC
        rewards = []
        discounted_reward = 0
        for reward, is_terminal in zip(reversed(memory.rewards), reversed(memory.is_terminals)):
            if is_terminal == 1:
                discounted_reward = 0
            discounted_reward = reward + (self.gamma * discounted_reward)
            rewards.insert(0, discounted_reward)
        
        rewards = torch.tensor(rewards).to(device)
        # Normalizing the rewards: MC
        #rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)  #MC use
        
        # convert list to tensor  截断所有旧网络出来的值，旧网络计算只会用到 logP
        old_states =torch.stack(memory.states).to(device).detach()
        old_states_img =torch.stack(memory.states_img).to(device).detach()
        old_states_next = torch.stack(memory.states_next).to(device).detach()
        old_states_img_next = torch.stack(memory.states_img_next).to(device).detach()  
        old_actions = torch.cat(memory.actions).to(device).detach()
        old_logprobs = torch.cat(memory.logprobs).to(device).detach() 
        
        with torch.autograd.set_detect_anomaly(True):
            # Evaluating old actions and values :
            state_values= self.critic(old_states, old_states_img).squeeze()
            state_next_values= self.critic_next(old_states_next,old_states_img_next) .squeeze()
            if done == 1:
                    state_next_values = state_next_values*0
            advantages = rewards.detach() + self.gamma *state_next_values.detach() - state_values   #TD use
            #advantages = rewards  - state_values  #MC use
            c_loss = (rewards.detach() + self.gamma *state_next_values.detach() - state_values).pow(2) 
            for _ in range(self.K_epochs):
                # ratio (ppi_theta/i_theta__old):
                # Surrogate Loss: # TD:r(s) + v(s+1) - v(s)  # MC = R-V（s）
                                
                action,logprobs,entropy = self.actor(old_states,old_states_img) 
                ratios = torch.exp(logprobs - old_logprobs.detach() ) #log转正数probability

                surr1 = ratios * advantages.detach()
                surr2 = torch.clamp(ratios, 1-self.eps_clip, 1+self.eps_clip) * advantages.detach()
                a_loss = -torch.min(surr1, surr2)  #+ 0.5*self.MseLoss(state_values, rewards) - 0.01*dist_entropy #均方损失函数
                self.A_optimizer.zero_grad()
                a_loss.backward() 
                self.A_optimizer.step()

            self.C_optimizer.zero_grad()
            c_loss.backward()
            self.C_optimizer.step()
            self.critic_next.load_state_dict(self.critic.state_dict())

        # Copy new weights into old policy: 更新时旧网络计算只会用到 logP,旧图没意义
        return advantages.pow(2) #advantages.sum().abs()/100 # MC use

def main():
    
    ############## Hyperparameters ##############
    update_timestep = 1     #TD use == 1 # update policy every n timesteps  set for TD
    K_epochs = 4           # update policy for K epochs  lr太大会出现NAN?
    eps_clip = 0.2            
    gamma = 0.9           
    
    episode =0

    sample_lr = [
        0.0001, 0.00009, 0.00008, 0.00007, 0.00006, 0.00005, 0.00004, 0.00003,
        0.00002, 0.00001, 0.000009, 0.000008, 0.000007, 0.000006, 0.000005,
        0.000004, 0.000003, 0.000002, 0.000001
    ]
    lr = 0.0001   #random_seed = None
    state_dim = 6
    action_dim = 1 
    #(self, state_dim, action_dim, lr, betas, gamma, K_epochs, eps_clip)
    actor_path = os.getcwd()+'/GAMA_python/PPO_Mixedinput_Navigation_Model/weight/ppo_TD3lstm_actor.pkl'
    critic_path = os.getcwd()+'/GAMA_python/PPO_Mixedinput_Navigation_Model/weight/ppo_TD3lstm_critic.pkl'
    ################ load ###################
    if episode >50  : #50 100
        lr = sample_lr[int(episode// 50)]

    ppo =  PPO(state_dim, action_dim, lr, gamma, K_epochs, eps_clip)
    if os.path.exists(actor_path):
        ppo.actor.load_state_dict(torch.load(actor_path))
        print('Actor Model loaded')
    if os.path.exists(critic_path):
        ppo.critic.load_state_dict(torch.load(critic_path))
        print('Critic Model loaded')
    print("Waiting for GAMA...")

    ################### initialization ########################
    save_curve_pic = os.getcwd()+'/GAMA_python/PPO_Mixedinput_Navigation_Model/result/PPO_3LSTM_loss_curve.png'
    save_critic_loss = os.getcwd()+'/GAMA_python/PPO_Mixedinput_Navigation_Model/training_data/PPO_TD3lstm_critic_loss.csv'
    save_reward = os.getcwd()+'/GAMA_python/PPO_Mixedinput_Navigation_Model/training_data/PPO_TD3lstm_reward.csv'
    reset()
    memory = Memory()

    advantages =0 #global value
    loss = []
    total_loss = []
    rewards = []
    total_rewards = []
    test = "GAMA"
    state,reward,done,time_pass,over = GAMA_connect(test) #connect
    #[real_speed/10, target_speed/10, elapsed_time_ratio, distance_left/100,distance_front_car/10,distance_behind_car/10,reward,done,over]
    print("done:",done,"timepass:",time_pass)
    ##################  start  #########################
    while over!= 1:
        #普通の場合
        if(done == 0 and time_pass != 0):  
            #print("state ",state)
            rewards.append(reward)
            memory.rewards.append(reward)
            memory.is_terminals.append(done)
            state = torch.DoubleTensor(state).reshape(1,6).to(device) 
            state_img = generate_img() 
            tensor_cv = torch.from_numpy(np.transpose(state_img, (2, 0, 1))).double().to(device)
            if  len(memory.states_next) ==0:
                for _ in range(3):
                    memory.states_next = memory.states
                    memory.states_next[2] = state
                    memory.states_img_next = memory.states_img
                    memory.states_img_next [2]= tensor_cv
            else:
                del memory.states_next[:1]
                del memory.states_img_next[:1]
                memory.states.append(state)
                memory.states_img_next.append(tensor_cv)
            loss_ = ppo.update(memory,lr,advantages,done)
            loss.append(loss_)
            del memory.logprobs[:]
            del memory.rewards[:]
            del memory.is_terminals[:]
            #memory.clear_memory()

            action = ppo.select_action(state,tensor_cv, memory)
            send_to_GAMA([[1,float(action*10)]])
            #print("acceleration ",float(action))

        # 終わり 
        elif done == 1:
            #先传后计算
            print("state_last",state)
            send_to_GAMA( [[1,0]] ) 
            rewards.append(reward) 

            del memory.states_next[:1]
            del memory.states_img_next[:1]
            state = torch.DoubleTensor(state).reshape(1,6).to(device) #转化成1行
            memory.states_next.append(state)
            state_img = generate_img() 
            tensor_cv = torch.from_numpy(np.transpose(state_img, (2, 0, 1))).double().to(device)
            memory.states_img_next.append(tensor_cv)

            memory.rewards.append(reward)
            memory.is_terminals.append(done)
            loss_ = ppo.update(memory,lr,advantages,done)
            loss.append(loss_)
            memory.clear_memory()

            print("----------------------------------Net_Trained---------------------------------------")
            print('--------------------------Iteration:',episode,'over--------------------------------')
            episode += 1
            loss_sum = sum(loss).cpu().detach().numpy()
            total_loss.append(loss_sum)
            total_reward = sum(rewards)
            total_rewards.append(total_reward)
            cross_loss_curve(loss_sum.squeeze(0),total_reward,save_curve_pic,save_critic_loss,save_reward)
            rewards = []
            loss = []
            if episode >50  : #50 100
                lr = sample_lr[int(episode// 50)]
            torch.save(ppo.actor.state_dict(),actor_path)
            torch.save(ppo.critic.state_dict(),critic_path)

        #最初の時
        else:
            print('Iteration:',episode)
            state = torch.DoubleTensor(state).reshape(1,6).to(device) 
            state_img = generate_img() # numpy image: H x W x C (500, 500, 3) -> (3,500,500)
            tensor_cv = torch.from_numpy(np.transpose(state_img, (2, 0, 1))).double().to(device) # np.transpose( xxx,  (2, 0, 1)) torch image: C x H x W
            action = ppo.select_action(state, tensor_cv,memory)
            print("acceleration: ",action) 
            send_to_GAMA([[1,float(action*10)]])

        state,reward,done,time_pass,over = GAMA_connect(test)

    return None 

if __name__ == '__main__':
    main()
 