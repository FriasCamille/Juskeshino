#!/usr/bin/env python3
import rospy
import rospkg
import time
from juskeshino_tools.JuskeshinoNavigation import JuskeshinoNavigation
from juskeshino_tools.JuskeshinoVision import JuskeshinoVision
from juskeshino_tools.JuskeshinoHardware import JuskeshinoHardware
from juskeshino_tools.JuskeshinoSimpleTasks import JuskeshinoSimpleTasks
from juskeshino_tools.JuskeshinoHRI import JuskeshinoHRI
from juskeshino_tools.JuskeshinoManipulation import JuskeshinoManipulation
from juskeshino_tools.JuskeshinoKnowledge import JuskeshinoKnowledge




def main():
    print("INITIALIZING CARRY MY LUGGAGE 2024 TEST NODE BY ITZEL...ヾ(๑╹◡╹)ﾉ")
    rospy.init_node("carry_my_luggage_test")
    rate = rospy.Rate(10)

    # Se subcribe a los servicios necesarios para manipulacion, navegacion,vision, etc...
    JuskeshinoNavigation.setNodeHandle()
    JuskeshinoVision.setNodeHandle()
    JuskeshinoHardware.setNodeHandle()
    JuskeshinoSimpleTasks.setNodeHandle()
    JuskeshinoHRI.setNodeHandle()
    JuskeshinoManipulation.setNodeHandle()
    JuskeshinoKnowledge.setNodeHandle()
    #JuskeshinoKnowledge.loadLocations(locations_file)

    print("ACT-PLN.-> Carry_my_luggage_test 2024")
    JuskeshinoHRI.say("I am ready for the carry my luggage test")
    JuskeshinoHRI.say("Please point at the bag that you want me to carry.")
    
    JuskeshinoHRI.say("Tell me, Justina yes, when you are pointing at the bag")
    time.sleep(1)
    
    voice = JuskeshinoHRI.waitForNewSentence(10)
    if "YES" in voice:
        print("ACT-PLN.->Pointing hand")
        if (JuskeshinoVision.pointingHand()):
            JuskeshinoHRI.say("Are you pointing at the left bag? tell me Justina yes or Justina no")
            if "YES" in voice: # L bag Justina yes
            #
                JuskeshinoNavigation.moveDistAngle(0.0, -0.2853, 10000)
                JuskeshinoHRI.say("Please put the left bag on the gripper")
            
            else:   # R bag Justina no
                JuskeshinoHRI.say("Are you pointing at the right bag? tell me Justina yes or Justina no")
                if "YES" in voice:
                    JuskeshinoNavigation.moveDistAngle(0.0, 0.2853, 10000)
                    JuskeshinoHRI.say("Please put the left bag on the gripper")
    
    print("ACT-PLN.-> Find person")
    #JuskeshinoHRI.enableLegFinder(True)

    print("legs found?", JuskeshinoHRI.frontalLegsFound())

    """
    if(not JuskeshinoHRI.frontalLegsFound()):
        print("ACT-PLN.-> Not found legs")
        JuskeshinoHRI.say("I can't found you, please stand in front of me")
        JuskeshinoHRI.enableHumanFollower(False)
    """





    return 
    while not rospy.is_shutdown():
        rate.sleep()


if __name__ == "__main__":
    main()
