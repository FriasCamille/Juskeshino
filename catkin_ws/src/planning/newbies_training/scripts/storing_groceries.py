#!/usr/bin/env python3
import rospy
import math
import numpy
import smach
import smach_ros
from juskeshino_tools.JuskeshinoNavigation import JuskeshinoNavigation
from juskeshino_tools.JuskeshinoHardware import JuskeshinoHardware
from juskeshino_tools.JuskeshinoSimpleTasks import JuskeshinoSimpleTasks
from juskeshino_tools.JuskeshinoVision import JuskeshinoVision
from juskeshino_tools.JuskeshinoHRI import JuskeshinoHRI
from juskeshino_tools.JuskeshinoManipulation import JuskeshinoManipulation
from juskeshino_tools.JuskeshinoKnowledge import JuskeshinoKnowledge
from sensor_msgs.msg import LaserScan
# TODO
    # 1. WAIT FOR THE DOOR TO OPEN         
    # 2. NAVIGATE TO THE TESTING AREA (TABLE)
    # 3. IDENTIFY TABLE
    # 4. CLASSIFY OBJECTS
    # 5. TAKE OBJECT FROM THE TABLE TO THE CABINET
    # 6. IDENTIFY CATEGORY IN CABINET
    # 7. LEAVE THE OBJECT IN THE CORRECT CATEGORY
                #    response = JuskeshinoVision.findTableEdge()
                # if response is None:
                #     JuskeshinoHRI.say("Ready for the next step")
                #     print("Cannot find the table")
                # else:
                # print(response)
class Wait_for_the_door(smach.State):
    def __init__(self):
        smach.State.__init__(self, 
                            outcomes=['succed', 'failed'])
        self.counter = 0

    # The input and output data of a state is called 'userdata'
    def execute(self,userdata):
        self.counter += 1
        if self.counter==1:
            rospy.logwarn('\n--> STATE 1 <: Wait for the door opened')

            #JuskeshinoHRI.say("Door is closed. Waiting for door to open")
            print("Door is closed. Waiting for door to open")
            rospy.sleep(2.5)


        msg = rospy.wait_for_message('/hardware/scan', LaserScan)
        if numpy.mean(msg.ranges[(int)(len(msg.ranges)*0.5 - 10):(int)(len(msg.ranges)*0.5 + 10)]) < 1.0:
            JuskeshinoHRI.say("The door is closed")
            print("The door is closed")
            self.counter = 0
            return 'failed'
        if numpy.mean(msg.ranges[(int)(len(msg.ranges)*0.5 - 10):(int)(len(msg.ranges)*0.5 + 10)]) > 1.0:
            JuskeshinoHRI.say("The door is opened")
            print("The door is opened")
            return 'succed'

class Navigate_to_table(smach.State):
    def __init__(self):
        smach.State.__init__(self, 
                            outcomes=['succed', 'failed'])
        self.counter = 0

        # The input and output data of a state is called 'userdata'
    def execute(self,userdata):
        self.counter += 1
        if self.counter==1:
            rospy.logwarn('\n--> STATE 2 <: Reaching the table')
            JuskeshinoHRI.say(" I am moving to the table")
            JuskeshinoNavigation.getClose(location, 300)
            #JuskeshinoNavigation.
class Find_table(smach.State):
    def __init__(self):
        smach.State.__init__(self, 
                            outcomes=['succed', 'failed'])
        self.counter = 0

        # The input and output data of a state is called 'userdata'
    def execute(self,userdata):
        self.counter += 1
        if self.counter==1:
            #Findin bounding table           
            response = JuskeshinoVision.findTableEdge()
            if response is None:
                JuskeshinoHRI.say("Ready for the next step")
                print("Cannot find the table")
                self.counter = 0
                return 'failed'
            else:
                print(response)
                return'succed'

def main():
    rospy.init_node("storing_groceries")
    rate = rospy.Rate(0.2)
    JuskeshinoNavigation.setNodeHandle()
    JuskeshinoHardware.setNodeHandle()
    JuskeshinoVision.setNodeHandle()
    JuskeshinoSimpleTasks.setNodeHandle()
    JuskeshinoManipulation.setNodeHandle()
    JuskeshinoHRI.setNodeHandle()
    JuskeshinoKnowledge.setNodeHandle()


    #-------------------CREATING SMACH state machine------------------------------

    rospy.loginfo('Starting state machine...')

    #   The outcome in the initialization of the state machine 'END' represents the 
    #    possible end point or result of the state machine's execution
    sm = smach.StateMachine(outcomes=['END'])

    # For viewing state machine (ROS)
    sis = smach_ros.IntrospectionServer('SMACH_VIEW_SERVER', sm, '/SM_STORING')
    sis.start()

    with sm:
        # Add states to the container
        smach.StateMachine.add('WAIT_FOR_THE_DOOR', Wait_for_the_door(), 
        transitions={'failed':'WAIT_FOR_THE_DOOR', 
                     'succed':'NAVIGATE_TO_TABLE'})
        smach.StateMachine.add('NAVIGATE_TO_TABLE', Navigate_to_table(), 
        transitions={'failed':'NAVIGATE_TO_TABLE', 
                     'succed':'FIND_TABLE'})
        smach.StateMachine.add('FIND_TABLE',Find_table(), 
        transitions={'failed':'FIND_TABLE', 
                     'succed':'END'})                 
        
  
    # Execute SMACH plan
    outcome = sm.execute()

    recog_objects, img = JuskeshinoVision.detectAndRecognizeObjects()
    for obj in recog_objects:
        print(obj.id)
        print(obj.pose.position)
        print(obj.header.frame_id)
        x,y,z = obj.pose.position.x, obj.pose.position.y, obj.pose.position.z
        x,y,z = JuskeshinoSimpleTasks.transformPoint(x,y,z, "shoulders_left_link", "base_link")
        print(x,y,z)
        PREPARE_TOP_GRIP  = [-1.25, 0.3, 0, 2.4, 0, 0.7,0]
        JuskeshinoHardware.moveLeftArmWithTrajectory(PREPARE_TOP_GRIP, 10)  # prepare 
        response=JuskeshinoManipulation.laIk([x,y,z,0,-1.5,0])

        #[response, success] = JuskeshinoManipulation.GripLa(obj)
        print(response)
    
if __name__ == "__main__":
    main()


