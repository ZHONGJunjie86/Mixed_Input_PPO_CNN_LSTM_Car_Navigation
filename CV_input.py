import csv
import matplotlib.pyplot as plt
import numpy as np
import os 
import cv2

location_NPC_front = os.getcwd()+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\GAMA_img\\save_NPC_front.csv'
location_NPC_behind = os.getcwd()+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\GAMA_img\\save_NPC_behind.csv'
location_NPC_closest_10 = os.getcwd()+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\GAMA_img\\save_NPC_closest_10.csv'
location_route = os.getcwd()+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\GAMA_img\\route.csv'
location_self =os.getcwd()+"\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\GAMA_img\\save_self.csv"
save_img = os.getcwd()+'\\GAMA_python\\PPO_Mixedinput_Navigation_Model\\GAMA_img\\save_agents.png'

def generate_img(): 
    error = True
    while error == True:
        try:
            NPC_front = []
            NPC_behind = []
            NPC_closest_10 = []
            Route = []
            SELF = []
            with open(location_NPC_front)as f:
                f_csv = csv.reader(f)
                for i in f_csv:
                    NPC_front = i
            with open(location_NPC_behind)as f:
                f_csv = csv.reader(f)
                for i in f_csv:
                    NPC_behind = i
            with open(location_NPC_closest_10)as f:
                f_csv = csv.reader(f)
                for i in f_csv:
                    NPC_closest_10 = i
            with open(location_route)as f:
                f_csv = csv.reader(f)
                for i in f_csv:
                    Route = i
            with open(location_self)as f:
                f_csv = csv.reader(f)
                for i in f_csv:
                    SELF = i

            NPC_front_X = []
            NPC_front_Y = []
            NPC_behind_X = []
            NPC_behind_Y = []
            NPC_closest_10_X = []
            NPC_closest_10_Y = []
            Route_X = []
            Route_Y = []
            count = 1
            for i in NPC_front:
                if count == 1 :
                    NPC_front_X.append(float(i[1:]))
                elif(count == 2):
                    NPC_front_Y.append(float(i))
                else:
                    count = 0
                count += 1

            for i in NPC_behind:
                if count == 1 :
                    NPC_behind_X.append(float(i[1:]))
                elif(count == 2):
                    NPC_behind_Y.append(float(i))
                else:
                    count = 0
                count += 1
            for i in NPC_closest_10:
                if count == 1 :
                    NPC_closest_10_X.append(float(i[1:]))
                elif(count == 2):
                    NPC_closest_10_Y.append(float(i))
                else:
                    count = 0
                count += 1
            for i in Route:
                if count == 1 :
                    try:
                        Route_X.append(float(i[1:]))
                    except(ValueError):
                        Route_X.append(float(i[2:]))
                elif(count == 2):
                    Route_Y.append(float(i))
                else:
                        count = 0
                count += 1
            plt.figure(figsize=(5, 5)) #500*500
            plt.axis('off') 
            plt.xlim(float(SELF[0][1:])-100,float(SELF[0][1:])+100)
            plt.ylim(float(SELF[1])-100, float(SELF[1])+100)
            plt.scatter(Route_X[0],Route_Y[0],color = 'g',marker = 'h') #start
            plt.scatter(Route_X[len(Route_X)-1],Route_Y[len(Route_Y)-1],color = 'purple',marker = 'h') #end
            plt.plot(Route_X,Route_Y,color = 'grey')   #route
            plt.scatter(NPC_behind_X, NPC_behind_Y,color = 'b',marker = 'o') #NPC_behind
            plt.scatter(NPC_front_X, NPC_front_Y,color = 'c',marker = '>') #NPC_front
            plt.scatter(NPC_closest_10_X, NPC_closest_10_Y,color = 'm',marker = 'P') #NPC_10
            plt.scatter(float(SELF[0][1:]), float(SELF[1]),color = 'r',marker= 'D')
            error = False
        except(IndexError,FileNotFoundError,ValueError,OSError,PermissionError):
            error = True
    
    plt.savefig(save_img, dpi=100)
    plt.close()
    img_cv = cv2.imread(save_img)   # cv2.imread()------np.array, (H x W xC), [0, 255], BGR
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    return img_cv
