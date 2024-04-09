#!/usr/bin/env python3
import rospy
import rospkg
import time
import numpy as np
from juskeshino_tools.JuskeshinoNavigation import JuskeshinoNavigation
from juskeshino_tools.JuskeshinoVision import JuskeshinoVision
from juskeshino_tools.JuskeshinoHardware import JuskeshinoHardware
from juskeshino_tools.JuskeshinoSimpleTasks import JuskeshinoSimpleTasks
from juskeshino_tools.JuskeshinoHRI import JuskeshinoHRI
from juskeshino_tools.JuskeshinoManipulation import JuskeshinoManipulation
from juskeshino_tools.JuskeshinoKnowledge import JuskeshinoKnowledge

HOME              = [0,0,0,0,0,0,0]
PREPARE           = [-0.69, 0.2, 0.0, 1.55, 0.0, 1.16, 0.0]
PREPARE_TOP_GRIP  = [-1.25, 0.3, 0, 2.4, 0, 0.7,0]
PREPARE_SERVING   = [0.91, 0.4, -0.5, 1.45, 0, 0.16, 0.5]
SERVING           = [0.91, 0.4, -0.5, 1.45, 0, 0.16, -1.6]
LEAVE_CEREAL      = [0.4, 0.18, -0.03, 1.45, 0, 0, 0]
LEAVE_MILK        = [0.4, -0.12, -0.03, 1.45, 0, 0, 0]
LEAVE_BOWL        = [0.4, -0.6, -0.03, 1.45, 0, 0, 0]
LEAVE_NEAR_CEREAL = [0.39, 0.18, -0.03, 1.45, 0, 0, 0]
EMPTYING_POSE     = [0.37, 0.57, -0.11, 1.68, -0.73, 0.76, -0.90]
LEAVE_NEAR_MILK   = [0.39, 0.18, -0.01, 1.42, 0, 0.37, 0]

MESA_INGREDIENTES = "breakfast_table" 
MESA_COMER        = "entrance_desk"

def serving_breakfast(object):
    print("PREPARE TOP")
    JuskeshinoHardware.moveLeftGripper(-0.5, 2.0)
    JuskeshinoHardware.moveLeftArmWithTrajectory(PREPARE_TOP_GRIP, 10)
    time.sleep(1)
    JuskeshinoHardware.moveLeftArmWithTrajectory(PREPARE_SERVING, 10)
    time.sleep(0.5)
    JuskeshinoHardware.moveLeftArmWithTrajectory(SERVING, 10)
    time.sleep(3)
    JuskeshinoHardware.moveLeftArmWithTrajectory(PREPARE_SERVING, 10)
    time.sleep(1)
    if object =="milk":
        JuskeshinoHardware.moveLeftArmWithTrajectory(LEAVE_MILK, 10)
        JuskeshinoHardware.moveLeftGripper(-0.5, 2.0)
    else:
        JuskeshinoNavigation.moveLateral(0.22, 10)
        JuskeshinoHardware.moveLeftArmWithTrajectory(LEAVE_CEREAL, 10)
        JuskeshinoHardware.moveLeftGripper(-0.5, 2.0)



def main():
    print("INITIALIZING SERVE BREAKFAST 2024 TEST BY ITZEL..............ヾ(๑╹◡╹)ﾉ")
    rospy.init_node("serve_breakfast_test")
    rate = rospy.Rate(10)

    rospack = rospkg.RosPack()
    locations_default = rospack.get_path("config_files") + "/known_locations_objects.yaml"

    print(locations_default)
    #locations_default = rospack.get_path("config_files") + "/known_locations_simul.yaml"
    locations_file = rospy.get_param("~locations", locations_default)

    # Se subcribe a los servicios necesarios para manipulacion, navegacion,vision, etc...
    JuskeshinoNavigation.setNodeHandle()
    JuskeshinoVision.setNodeHandle()
    JuskeshinoHardware.setNodeHandle()
    JuskeshinoSimpleTasks.setNodeHandle()
    JuskeshinoHRI.setNodeHandle()
    JuskeshinoManipulation.setNodeHandle()
    JuskeshinoKnowledge.setNodeHandle()
    JuskeshinoKnowledge.loadLocations(locations_file)


    # Esperar a que se abra la puerta
    JuskeshinoHRI.say("I'm waiting for the door to be open")
    """
    if not JuskeshinoSimpleTasks.waitForTheDoorToBeOpen(300):
        print("ACT-PLN.->Door never opened")
        return
    JuskeshinoHRI.say("I can see now that the door is open")
    # Ir a la cocina
    """
    pila = ["bowl", "cereal", "milk"] 
    #pila = ["milk", "milk", "milk"]        

    #pila = ["apple", "pringles", "soda"]
    
    count = 0
    while count < 3: # Revisa pila
        
        print("OBJECT", pila[count])
        actual_obj = pila[count]
        # Ir a locacion de ingredientes
        JuskeshinoHRI.say("I'm going to the kitchen position.")
        print("I'm going to the "+MESA_INGREDIENTES+" position.")

        #if not JuskeshinoNavigation.getClose("desk", 150):
        if not JuskeshinoNavigation.getClose(MESA_INGREDIENTES, 100):  #*******************
            print("SB-PLN.->Cannot get close to the "+MESA_INGREDIENTES+" position")

        time.sleep(2)
        # Alinearse con mueble
        print("SB-PLN.->move head")
        if not JuskeshinoHardware.moveHead(0,-1, 5):
            print("SB-PLN.->Cannot move head")
            time.sleep(0.5)
            JuskeshinoHardware.moveHead(0,-1, 5)


        time.sleep(2)
        if not JuskeshinoSimpleTasks.alignWithTable():
            print("SB-PLN.->Cannot align with table")

        # Busqueda y reconocimiento del objeto
        time.sleep(1)
        print("SB-PLN.->Trying to detect object: ")
        JuskeshinoHRI.say("I'm trying to detect the object:____", actual_obj)
        
        [obj, img] = JuskeshinoSimpleTasks.object_search(actual_obj)   #**************************
        if obj == None: 
            print("Object not found...........")

        else:
            print("SB-PLN.->Detected object : " + str([obj.id, obj.category, obj.object_state, obj.pose.position]))
            JuskeshinoHRI.say("I found the object, I'm going to try to grasp them")
            # Colocandose en posicion de agarre
            
            print("SB-PLN.->handling location ")
            JuskeshinoSimpleTasks.handling_location(obj)
            time.sleep(1)
            print("SB-PLN.->move head")
            if not JuskeshinoHardware.moveHead(0,-1, 5):
                print("SB-PLN.->Cannot move head")
                time.sleep(0.5)
                JuskeshinoHardware.moveHead(0,-1, 5)
                time.sleep(1)
            

            j = 0
        
            while j < 4:
                # reconocimiento objeto
                [obj, img] = JuskeshinoVision.detectAndRecognizeObject(actual_obj) #**************************
                print("SB-PLN.->Detected object : " + str([obj.id, obj.category, obj.object_state, obj.pose.position]))
                # Tomar objeto                                              
                print("SB-PLN.->Sending goal traj to prepare")
                print("PREPARE HIGHT")
                JuskeshinoHardware.moveLeftArmWithTrajectory(PREPARE_TOP_GRIP , 10)
                time.sleep(1)
                print("SB-PLN.->Open gripper")
                if actual_obj == "bowl": JuskeshinoHardware.moveLeftGripper(0.4 , 3.0)
                else: JuskeshinoHardware.moveLeftGripper(0.7, 3.0)
                time.sleep(1)
                print("SB-PLN.-> Call Best Grasping Configuration Service")
                
                [resp, graspable] = JuskeshinoManipulation.planBestGraspingConfiguration(obj)
                if graspable:
                    print("SB-PLN.->object position", obj.pose.position)
                    print("SB-PLN.->Sending best gripper configuration")
                    time.sleep(1)
                    JuskeshinoHardware.moveLeftArmWithTrajectory(resp.articular_trajectory,10)
                    print("SB-PLN.->Closing gripper first attempt")
                    JuskeshinoHardware.moveLeftGripper(-0.5, 2.0) 
                    break

                else:
                    print("SB-PLN.->No possible poses found")
                j = j+1

            print("SB-PLN.->Moving base backwards")
            JuskeshinoHRI.say("I'have grasped the object")
            JuskeshinoNavigation.moveDist(-0.3, 10)
            time.sleep(1)
            print("ACT-PLN.->Moving arm to prepare***")
            JuskeshinoHardware.moveLeftArmWithTrajectory(PREPARE, 10)  # prepare
    
            actual_obj = pila[count]
            count = count + 1
            print("Actual object: ", actual_obj)
            # Ir a la mesa del desayuno
        
        
        print("SB-PLN.->Getting close to " + MESA_COMER + "location")
        JuskeshinoHRI.say("I'm going to the location")

        if not JuskeshinoNavigation.getClose(MESA_COMER, 100):  #**********************************
        #if not JuskeshinoNavigation.getClose("cupboard", 100):
            print("SB-PLN.->Cannot get close to " + MESA_COMER +" position")
    
        JuskeshinoHRI.say("I have arrived at the" + MESA_COMER + " location")
        time.sleep(1)
        print("SB-PLN.->move head")
        if not JuskeshinoHardware.moveHead(0,-1, 5):
            print("SB-PLN.->Cannot move head")
            time.sleep(0.5)
            JuskeshinoHardware.moveHead(0,-1, 5)
        
        time.sleep(2)
        # Se alinea con la mesa
        JuskeshinoHRI.say("I'M GOING TO LINE UP WITH THE TABLE")
        print("SB-PLN.->Aligning with table")
        JuskeshinoSimpleTasks.alignWithTable()
    
        # Retrocede
        time.sleep(1)
        print("SB-PLN.->Moving base backwards")
        JuskeshinoNavigation.moveDist(-0.3, 10)

        # lleva  brazo a posicion por encima de la mesa
        print("SB-PLN.->Moving left arm to deliver position")
        JuskeshinoHRI.say("I'm going to leave the object")

        if (actual_obj == "milk") or (actual_obj == "cereal"):
            serving_breakfast(actual_obj) 

        if actual_obj == "bowl":
            JuskeshinoHRI.say("Arm prepare")
            JuskeshinoHardware.moveLeftArmWithTrajectory(PREPARE_TOP_GRIP , 12) 
            time.sleep(1)
            JuskeshinoHRI.say("Arm bowl")
            JuskeshinoHardware.moveLeftArmWithTrajectory(LEAVE_BOWL , 12)
            time.sleep(1)
            # se mueve hacia delante 0.3 m
            print("SB-PLN.->Moving base backwards")
            JuskeshinoHRI.say("I'm going to place the object on the table")
            JuskeshinoNavigation.moveDist(0.3, 7)
            # Soltar el objeto
            time.sleep(1)
            print("SB-PLN.->Open gripper")
            JuskeshinoHardware.moveLeftGripper(0.7, 2.0)
            time.sleep(1)            # Soltar el objeto
            

        if (actual_obj == "pringles") or (actual_obj == "soda"):
            serving_breakfast(actual_obj)

        if actual_obj == "apple":
            JuskeshinoHardware.moveLeftArmWithTrajectory(LEAVE_BOWL , 10) 


        # Moverse para atras
        print("SB-PLN.->Moving base backwards")
        JuskeshinoNavigation.moveDist(-0.3, 7)
        time.sleep(1)
        print("SB-PLN.->Moving left arm to prepare")
        JuskeshinoHardware.moveLeftArmWithTrajectory(PREPARE , 10)
        #JuskeshinoHardware.moveLeftArmWithTrajectory(HOME , 10)
    
    
    # El desayuno esta servido 
    JuskeshinoHRI.say("I finished the test")
    


    return 
    while not rospy.is_shutdown():
        rate.sleep()


if __name__ == "__main__":
    main()


	
