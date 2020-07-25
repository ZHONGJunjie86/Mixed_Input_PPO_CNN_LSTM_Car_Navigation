import numpy as np 
import os 
import random
ad1 = 'D:/Software/PythonWork/GAMA_python/PPO_Mixedinput_Navigation_Model/GAMA_R/python_AC_1.csv'
ad2 = 'D:/Software/PythonWork/GAMA_python/PPO_Mixedinput_Navigation_Model/GAMA_R/python_AC_2.csv'
def main():
    if(os.path.exists(ad1) == False or
       os.path.exists(ad2) == False): #
        data = []
        data.append(0)
        return data
    elif(os.stat(ad1).st_size == 0 or 
         os.stat(ad2).st_size == 0): #
        data = []
        data.append(0)
        return data
    else:
        try:
            if(random.random()>0.51):
                state = np.loadtxt(ad1, delimiter=",")  
            else:
                state = np.loadtxt(ad2, delimiter=",")
            data = []
            data.append(0)
            if(state.size == 1):
                data.append(state)
                return data
            elif(state.size == 2):
                #data.append(state[0])
                #data.append(state[1])  直接传 state[0]类型错误
                a = float(state[0])
                b = float(state[1])
                return [a,b]        #data
            else:
                return data
        except(ValueError):
            data = []
            data.append(0)
            return data


if __name__ == '__main__':
    main()