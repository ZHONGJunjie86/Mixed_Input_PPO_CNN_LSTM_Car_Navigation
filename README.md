# Mixed_Input_PPO_CNN_LSTM_Car_Navigation
A car-agent navigates in complex traffic conditions by Mixed_Input_PPO_CNN_LSTM model.  
# Feature extraction and image inverse generation
![image](https://github.com/ZHONGJunjie86/Mixed_Input_PPO_CNN_LSTM_Car_Navigation/blob/master/result/old/img_generante.JPG)
![image](https://github.com/ZHONGJunjie86/PPO_LSTM_Car_Navigation/blob/master/result/old/ppo-mixed.gif)
# Mixed input architecture
![image](https://github.com/ZHONGJunjie86/Mixed_Input_PPO_CNN_LSTM_Car_Navigation/blob/master/result/achitecture_new.png)
![image](https://github.com/ZHONGJunjie86/Mixed_Input_PPO_CNN_LSTM_Car_Navigation/blob/master/result/architecture3.png)
# Traffic conditions && Collision Detection
When a car-agent navigates on the road, it may encounter with other cars.   
In some conditions, the acceleration chosen by car-agent will cause jam or collision.  
Since the condition will come very complex and the GAMA simulator has no idea about the collision so I have to make collision detection or jam detection.  
Here will choose the closest 10 cars around the agent and calculate the distances.   
These equations are neccessary. And here will use Euclidean distance for safe driving.   
<a href="https://www.codecogs.com/eqnedit.php?latex=S&space;=&space;v_{0}*t&space;&plus;&space;\frac{1}{2}at^{2}" target="_blank"><img src="https://latex.codecogs.com/gif.latex?S&space;=&space;v_{0}*t&space;&plus;&space;\frac{1}{2}at^{2}" title="S = v_{0}*t + \frac{1}{2}at^{2}" /></a>     
<a href="https://www.codecogs.com/eqnedit.php?latex=v_{n&plus;1}&space;=&space;v_{n}&plus;a_{n}t_{n}" target="_blank"><img src="https://latex.codecogs.com/gif.latex?v_{n&plus;1}&space;=&space;v_{n}&plus;a_{n}t_{n}" title="v_{n+1} = v_{n}+a_{n}t_{n}" /></a>  

## On the same road
First, the agent compute the useful distances (There will be distance of the behind car or distance of the front car).   
And then detections will be executed after the agent choose acceleration to detecte whether the acceleration will cause jams or collisions.    
A unit of time is 1-cycle.  
### Collision Detection
When there is an another car is in front of the car-agent when the two cars are on the same road, if   
<a href="https://www.codecogs.com/eqnedit.php?latex=EuclideanDistance&space;&plus;&space;v_{car}*t&space;\leq&space;v_{agent}*t&plus;\frac{1}{2}*a*t^{2}" target="_blank"><img src="https://latex.codecogs.com/gif.latex?EuclideanDistance&space;&plus;&space;v_{car}*t&space;\leq&space;v_{agent}*t&plus;\frac{1}{2}*a*t^{2}" title="EuclideanDistance&space;&plus;&space;v_{car}*t&space;\leq&space;v_{agent}*t&plus;\frac{1}{2}*a*t^{2}" /></a>     
the acceleration will be supposed to cause collision with the front cars. (The front cars maybe more than one.)                         
### Jam Detection
When there is an another car is behind of the car-agent when the two cars are on the same road, if     
<a href="https://www.codecogs.com/eqnedit.php?latex=EuclideanDistance&space;&plus;&space;v_{agent}*t&plus;\frac{1}{2}*a*t^{2}&space;\leq&space;v_{car}*t" target="_blank"><img src="https://latex.codecogs.com/gif.latex?EuclideanDistance&space;&plus;&space;v_{agent}*t&plus;\frac{1}{2}*a*t^{2}&space;\leq&space;v_{car}*t" title="EuclideanDistance + v_{agent}*t+\frac{1}{2}*a*t^{2} \leq v_{car}*t" /></a>    
the acceleration will be supposed to cause jam with the behind cars. (The behind cars maybe more than one.)  
#### Jam
![image](https://github.com/ZHONGJunjie86/PPO_LSTM_Car_Navigation/blob/master/result/old/jam.JPG)   
## On the different road
The calculation process is the same as the conditions on the same road.But the conditions become very complex.  
The closest 10 cars will on the same road with the agnet?   
If so, will the cars be the front of the agent or behind of the agent?   
These conditions will be detected clear in the gaml file.
# Station representation
[real_speed/10, target_speed/10, elapsed_time_ratio, distance_to_goal/100,distance_front_car/10,distance_behind_car/10]  
# Action representation
The network's output are accelerations which are constricted between [-5,8]m/s^2 to be closer to the real situations.
# Reward shaping
　Output accelerate.
　Action representation [acceleration].
  
　The car will learn to control its accelerate with the restructions shown below:  
　Reward shaping:  
* rt = r terminal + r danger + r speed  
* r terminal： -0.013(target_speed > real_speed) or  -0.01(target_speed < real_speed)：crash / time expires 
                 0.005:non-terminal state  
* r speed： related to the target speed  
* if sa ≤st: 0.05 - 0.036*(target_speed / real_speed) 
* if sa > st: 0.05 - 0.033*(real_speed / target_speed ) 

　In my experiment it's obviously I desire the agent to learn controling its speed around the target-speed.   
# PPO2
<a href="https://www.codecogs.com/eqnedit.php?latex=J^{\theta&space;'}(\theta&space;)&space;=&space;\sum&space;min(\frac{p_{\theta'&space;}}{p_{\theta&space;}}*A_{\theta&space;}(s_{t&space;},a_{t&space;})),clip(\frac{p_{\theta'&space;}}{p_{\theta&space;}},1-\varepsilon&space;,1&plus;\varepsilon)*A_{\theta&space;}(s_{t&space;},a_{t&space;}))" target="_blank"><img src="https://latex.codecogs.com/gif.latex?J^{\theta&space;'}(\theta&space;)&space;=&space;\sum&space;min(\frac{p_{\theta'&space;}}{p_{\theta&space;}}*A_{\theta&space;}(s_{t&space;},a_{t&space;})),clip(\frac{p_{\theta'&space;}}{p_{\theta&space;}},1-\varepsilon&space;,1&plus;\varepsilon)*A_{\theta&space;}(s_{t&space;},a_{t&space;}))" title="J^{\theta&space;'}(\theta&space;)&space;=&space;\sum&space;min(\frac{p_{\theta'&space;}}{p_{\theta&space;}}*A_{\theta&space;}(s_{t&space;},a_{t&space;})),clip(\frac{p_{\theta'&space;}}{p_{\theta&space;}},1-\varepsilon&space;,1&plus;\varepsilon)*A_{\theta&space;}(s_{t&space;},a_{t&space;}))" /></a>
### TD
<a href="https://www.codecogs.com/eqnedit.php?latex=\bigtriangledown&space;Advantage&space;=&space;\frac{1}{N}\sum_{n=1}^{N}\sum_{t=1}^{T}(r_{t}&plus;V_{s&plus;1}^{n}-V_{s}^{n})" target="_blank"><img src="https://latex.codecogs.com/gif.latex?\bigtriangledown&space;Advantage&space;=&space;\frac{1}{N}\sum_{n=1}^{N}\sum_{t=1}^{T}(r_{t}&plus;V_{s&plus;1}^{n}-V_{s}^{n})" title="\bigtriangledown&space;Advantage&space;=&space;\frac{1}{N}\sum_{n=1}^{N}\sum_{t=1}^{T}(r_{t}&plus;V_{s&plus;1}^{n}-V_{s}^{n})" /></a>
### MC
<a href="https://www.codecogs.com/eqnedit.php?latex=\bigtriangledown&space;Advantage&space;=&space;\frac{1}{N}\sum_{n=1}^{N}\sum_{t=1}^{T}(R_{t}-V_{s}^{n})" target="_blank"><img src="https://latex.codecogs.com/gif.latex?\bigtriangledown&space;Advantage&space;=&space;\frac{1}{N}\sum_{n=1}^{N}\sum_{t=1}^{T}(R_{t}-V_{s}^{n})" title="\bigtriangledown&space;Advantage&space;=&space;\frac{1}{N}\sum_{n=1}^{N}\sum_{t=1}^{T}(R_{t}-V_{s}^{n})" /></a>
### Actor Critic (TD)
　<a href="https://www.codecogs.com/eqnedit.php?latex=\bigtriangledown&space;R&space;=&space;\frac{1}{N}\sum_{n=1}^{N}\sum_{t=1}^{T}(r_{t}&plus;V_{s&plus;1}^{n}-V_{s}^{n})\bigtriangledown&space;log&space;P_{\Theta&space;}(a_{t}^{n}|s_{t}^{n})" target="_blank"><img src="https://latex.codecogs.com/gif.latex?\bigtriangledown&space;R&space;=&space;\frac{1}{N}\sum_{n=1}^{N}\sum_{t=1}^{T}(r_{t}&plus;V_{s&plus;1}^{n}-V_{s}^{n})\bigtriangledown&space;log&space;P_{\Theta&space;}(a_{t}^{n}|s_{t}^{n})" title="\bigtriangledown R = \frac{1}{N}\sum_{n=1}^{N}\sum_{t=1}^{T}(r_{t}+V_{s+1}^{n}-V_{s}^{n})\bigtriangledown log P_{\Theta }(a_{t}^{n}|s_{t}^{n})" /></a>
# About GAMA
　The GAMA is a platefrom to do simulations.      
　I have a GAMA-modle "simple_intersection.gaml", which is assigned a car and some traffic lights. The model will sent some data  
　[real_speed, target_speed, elapsed_time_ratio, distance_to_goal,reward,done,time_pass,over]  
　as a matrix to python environment, calculating the car's accelerate by A2C. And applying to the Markov Decision Process framework, the car in the GAMA will take up the accelerate and send the latest data to python again and over again until  reaching the destination.
