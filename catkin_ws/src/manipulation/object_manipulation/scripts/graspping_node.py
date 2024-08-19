#!/usr/bin/env python3
import rospy
import numpy as np
import tf.transformations as tft
import tf2_ros
import tf
import math
from geometry_msgs.msg import PoseStamped, Point, PointStamped, Pose
from vision_msgs.srv import *
from manip_msgs.srv import *
from visualization_msgs.msg import Marker, MarkerArray
import geometry_msgs.msg


MAXIMUM_GRIP_LENGTH = 0.16
MINIMUM_HEIGHT_PRISM = 0.17
MAXIMUM_CUBE_SIZE = 0.16
Z_OFFSET_CUB = 0.08# real 0.12
Z_OFFSET_CUB_2 = 0.01
Z_OFFSET_PRISM = 0.21
Z_OFFSET_PRISM_2 = 0.07
Z_OFFSET_BOWL  = 0.304#0.22#0.19
Z_OFFSET_BOWL_2  = 0.07#0.07


def generate_tf_msg(tf_):
    tf_.orientation.x = 0.0
    tf_.orientation.y = 0.0
    tf_.orientation.z = 0.0
    tf_.orientation.w = 1.0


def points_actual_to_points_target(point_in, f_actual, f_target):
    global listener
    point_msg                 = PointStamped()  
    point_msg.header.frame_id = f_actual   # frame de origen
    point_msg.header.stamp    = rospy.Time() # la ultima transformacion
    point_msg.point.x         = point_in[0]
    point_msg.point.y         = point_in[1]
    point_msg.point.z         = point_in[2]

    listener.waitForTransform(f_actual, f_target, rospy.Time(), rospy.Duration())
    point_target_frame        = listener.transformPoint(f_target, point_msg)
    new_point                 = point_target_frame.point
    return [ new_point.x , new_point.y , new_point.z ]



def pose_actual_to_pose_target(pose, f_actual, f_target):
    global listener
    poseStamped_msg = PoseStamped()  
    poseStamped_msg.header.frame_id = "object"   # frame de origen
    poseStamped_msg.header.stamp = rospy.Time()  # la ultima transformacion
    poseStamped_msg.pose = pose

    try:
        listener.waitForTransform("object", "shoulders_left_link", rospy.Time(0), rospy.Duration(10.0))
        print("waitfor ..despues")
        new_poseStamped = listener.transformPose('shoulders_left_link', poseStamped_msg)
        new_pose = new_poseStamped.pose
        return new_pose
    
    except:
        print("Best_Grasp_Node.-> Could not get the pose in the desired frame")
        return -1



def pose_for_ik_service(pose_in_frame_object):  
    """
    Cambia a los candidatos de agarre del sistema 'object' al sistema del brazo izquierdo
    y regresa un arreglo [x,y,z,R,P,Y], si no lo consiguió retorna el valor -1
    """
    print("In pose-for_ik_service")
    new_pose = pose_actual_to_pose_target(pose_in_frame_object, 'object' , 'shoulders_left_link') 

    if new_pose == -1:
        return -1, -1

    x , y, z = new_pose.position.x , new_pose.position.y , new_pose.position.z
    roll,pitch,yaw = tft.euler_from_quaternion( [new_pose.orientation.x , new_pose.orientation.y , 
                                          new_pose.orientation.z , new_pose.orientation.w ])
    cartesian_pose_shoulder = np.asarray([x ,y ,z , roll, pitch , yaw])
    return cartesian_pose_shoulder, new_pose



def marker_array_publish(pointxyz, target_frame, count, id):
    #print("point grip", pointxyz)
    global marker_array_pub
    MARKERS_MAX = 100
    marker_array = MarkerArray()
    marker = Marker()
    marker.header.frame_id = target_frame
    marker.type = marker.SPHERE
    marker.action = marker.ADD
    marker.scale.x , marker.scale.y,marker.scale.z = 0.03, 0.03, 0.03
    marker.color.a , marker.color.r, marker.color.g, marker.color.b = 1.0, 1.0 , 0.0 ,1.0
    marker.pose.orientation.w = 1.0
    marker.pose.position.x, marker.pose.position.y, marker.pose.position.z = pointxyz[0], pointxyz[1], pointxyz[2]
    
    if(count > MARKERS_MAX): marker_array.markers.pop(0)
    marker_array.markers.append(marker)
    # Renumber the marker IDs
    for m in marker_array.markers:
        m.id = id
        id += 1
    # Publish the MarkerArray
    marker_array_pub.publish(marker_array)



def broadcaster_frame_object(frame, child_frame, pose):
    br = tf2_ros.TransformBroadcaster()
    t = geometry_msgs.msg.TransformStamped()
    t.header.frame_id = frame
    t.child_frame_id = child_frame 
    t.header.stamp = rospy.Time.now()
    t.transform.translation.x = pose.position.x
    t.transform.translation.y = pose.position.y
    t.transform.translation.z = pose.position.z
    t.transform.rotation.x = pose.orientation.x
    t.transform.rotation.y = pose.orientation.y
    t.transform.rotation.z = pose.orientation.z
    t.transform.rotation.w = pose.orientation.w
    br.sendTransform(t)
















def generates_candidates(grip_point , obj_pose, rotacion, obj_state , name_frame, step, num_candidates, type_obj = None, offset = 0):    
    global debug 
    j = 0

    if (obj_state == "horizontal") or (type_obj == "BOWL") or (type_obj == "BOX") or (type_obj == "CUBIC"):   # 13 cm por encima del objeto (z_base_link)
        grip_point_bl = points_actual_to_points_target(grip_point, 'object', 'base_link')

        if type_obj == "BOWL":
            grip_point_bl[2] = grip_point_bl[2] + Z_OFFSET_BOWL

        else:
            if (type_obj == "BOX") or (type_obj == "CUBIC"):
                #print("BOX OR CUBE Z OFFSET")
                grip_point_bl[2] = grip_point_bl[2] + Z_OFFSET_CUB
            else:
                grip_point_bl[2] = grip_point_bl[2] + Z_OFFSET_PRISM
                #print("HORIZONTAL PRISM POINT OFFSET.................")

        #print("PUNTO CENTROIDE", grip_point_bl)

        grip_point = points_actual_to_points_target(grip_point_bl, 'base_link', 'object')
        if debug:
            marker_array_publish(grip_point, 'object', 59, 56)


    grasp_candidates_quaternion = []
    q_gripper = []

    R, P, Y = tft.euler_from_quaternion([obj_pose.orientation.x ,  # pose expresada en RPY para realizar rotaciones
                                             obj_pose.orientation.y ,
                                             obj_pose.orientation.z, 
                                             obj_pose.orientation.w])
    if rotacion == "P": 
        P = np.deg2rad(offset) #horizontal grip#
    else:
        if rotacion == "R": R = R + np.deg2rad(offset) #vertical grip
    
    for j in range(num_candidates):      # genera candidatos
        obj_pose_frame_object = Pose()
        obj_pose_frame_object.orientation.x = 0
        obj_pose_frame_object.orientation.y = 0
        obj_pose_frame_object.orientation.z = 0
        obj_pose_frame_object.orientation.w = 1
        obj_pose_frame_object.position.x = 0
        obj_pose_frame_object.position.y = 0
        obj_pose_frame_object.position.z = 0
        q_gripper = tft.quaternion_from_euler(R,P,Y,'sxyz')  # Pose en frame 'object' cuaterniones
        obj_pose_frame_object.orientation.x = q_gripper[0]
        obj_pose_frame_object.orientation.y = q_gripper[1]
        obj_pose_frame_object.orientation.z = q_gripper[2]
        obj_pose_frame_object.orientation.w = q_gripper[3]
        
        if rotacion == "P": 
            P = P + np.deg2rad(step) + np.deg2rad(offset) #horizontal grip#
        else:
            if rotacion == "R": R = R + np.deg2rad(step) + np.deg2rad(offset) #vertical grip
        
        obj_pose_frame_object.position.x = grip_point[0]
        obj_pose_frame_object.position.y = grip_point[1]
        obj_pose_frame_object.position.z = grip_point[2]
        
        if debug:
            #print("Best_Grasp_Node.-> emitiendo pose........." + name_frame+str(j)+obj_state , grip_point)
            broadcaster_frame_object('object', name_frame+str(j)+obj_state , obj_pose_frame_object )
        
        grasp_candidates_quaternion.append(obj_pose_frame_object )     # guarda el candidato en frame bl
        
    return grasp_candidates_quaternion  # REGRESA A LOS CANDIDATOS EN FRAME OBJECT





def initial_pose(obj_pose, obj_state , grip_point, size, type_obj):
    global debug

    grip_tf = Pose()
    #grip_tf.position.x, grip_tf.position.y, grip_tf.position.z = grip_point[0], grip_point[1], grip_point[2]
    num_candidates = 3 # debe ser par
    offset = -85
    name_frame = "CUBIC"
    step = -5
        
    generate_tf_msg(grip_tf)

    pose_list = generates_candidates(grip_point , grip_tf, "P", obj_state ,  name_frame, step, num_candidates, type_obj, offset)

    return pose_list 


def bowl(obj_pose, obj_state , grip_point, size, type_obj):
    grip_point = [-0.02 , size.z/2 , 0]
    first_trajectory = initial_pose(obj_pose, obj_state , grip_point, size, type_obj)
    total_traj = first_trajectory
    return total_traj


def cubic(obj_pose, obj_state , grip_point, size, type_obj):
    grip_point = [0,0,0]
    candidate_list = initial_pose(obj_pose, obj_state , grip_point, size, type_obj)
    return evaluating_possibility_grip(candidate_list , obj_state, type_obj)


def prism_horizontal(obj_pose, obj_state , grip_point, size, type_obj):
    grip_point = [0,0,0]
    candidate_list = initial_pose(obj_pose, obj_state , grip_point, size, type_obj)
    total_traj = first_trajectory =  evaluating_possibility_grip(candidate_list , obj_state, type_obj)
    # Falta agregar rotacion de la muneca
    total_traj = first_trajectory
    return total_traj


def prism_vertical(obj_pose, obj_state , grip_point, size, type_obj):
    global debug

    grip_tf = Pose()
    grip_tf.position.x, grip_tf.position.y, grip_tf.position.z = 0, 0, 0
    num_candidates = 36 # debe ser par
    offset = -90
    name_frame = "CUBIC"
    step = -10
        
    generate_tf_msg(grip_tf)
    pose_list = generates_candidates([grip_tf.position.x , grip_tf.position.y , grip_tf.position.z] , grip_tf, "R", obj_state ,  name_frame, step, num_candidates, type_obj, offset)

    return 



def grip_rules(obj_pose, type_obj, obj_state, size, grip_point):
    
    if(type_obj == "BOWL"):
        print("Best_Grasp_Node.->The object will be GRABBED AS BOWL.................")
        return bowl(obj_pose, obj_state , grip_point, size, type_obj)
    

    if(type_obj == "CUBIC"):
        print("Best_Grasp_Node.->The object will be GRABBED AS CUBE.................")
        return cubic(obj_pose, obj_state , grip_point, size, type_obj)


    if(type_obj == "PRISM"):
        print("Best_Grasp_Node.->The object will be GRABBED AS PRISM..................")
        if obj_state == 'horizontal':
            return prism_horizontal(obj_pose, obj_state , grip_point, size, type_obj)
        else:
            return prism_vertical(obj_pose, obj_state)
        
        """
    if(type_obj == "SPOON"):
        print("Best_Grasp_Node.->The object will be GRABBED AS BOWL.................")
        return spoon(obj_pose, obj_state , grip_point, size, type_obj)

    if(type_obj == "BOX"):
        print("Best_Grasp_Node.->The object will be GRABBED AS BOWL.................")
        return spoon(obj_pose, obj_state , grip_point, size, type_obj)

    if(type_obj == "DISH"):
        print("Best_Grasp_Node.->The object will be GRABBED AS BOWL.................")
        return spoon(obj_pose, obj_state , grip_point, size, type_obj)
        """

    else:
        print("Error identificando forma del objeto.................")
        poses_list = []
        return None, None, False
    


def build_trajectory():
    print("...")




def evaluating_possibility_grip(candidate_q_list, obj_state, category):
    global ik_srv
    ik_msg = InverseKinematicsPose2TrajRequest()

    print("Best_Grasp_Node.-> evaluating_possibility_grip()")
    

    for candidate in candidate_q_list:  # rellena el mensaje para el servicio IK
        candidate_ik_msg, candidate_tf = pose_for_ik_service(candidate)

        ik_msg.x         = candidate_ik_msg[0] 
        ik_msg.y         = candidate_ik_msg[1]
        ik_msg.z         = candidate_ik_msg[2]
        ik_msg.roll      = candidate_ik_msg[3]     
        ik_msg.pitch     = candidate_ik_msg[4]
        ik_msg.yaw       = candidate_ik_msg[5]
                
        ik_msg.duration  = 0
        ik_msg.time_step = 0.05
        try:
            resp_ik_srv = ik_srv(ik_msg)    # Envia al servicio de IK
            print("Best_Grasp_Node.-> Suitable pose for object .....................")
            return resp_ik_srv.articular_trajectory , candidate_tf , True
        except:
            print("Best_Grasp_Node.-> Candidato no aprobado")
            continue

    return None, None, False





def callback(req):
    global listener
    resp = BestGraspTrajResponse() 

    """
    pose_list_quaternion = grip_rules(req.recog_object.pose, 
                                      req.recog_object.category, 
                                      req.recog_object.object_state  , 
                                      req.recog_object.size , 
                                      [req.recog_object.pose.position.x, req.recog_object.pose.position.y, req.recog_object.pose.position.z] )
    
    if len( pose_list_quaternion) <= 0:
        print("Best_Grasp_Node.-> object is no graspable")
        return resp
    
    trajectory, pose, graspable = evaluating_possibility_grip(pose_list_quaternion , 
                                                              req.recog_object.object_state, 
                                                              req.recog_object.category)
   """
    trajectory, pose, graspable = grip_rules(req.recog_object.pose, 
                                      req.recog_object.category, 
                                      req.recog_object.object_state  , 
                                      req.recog_object.size , 
                                      [req.recog_object.pose.position.x, req.recog_object.pose.position.y, req.recog_object.pose.position.z] )
        

    if graspable:
        print("Best_Grasp_Node.-> SUITABLE POSE FOR OBJECT MANIPULATION......")
        broadcaster_frame_object('shoulders_left_link', 'suitable_pose' , pose)
        resp.articular_trajectory = trajectory  # Retorna trayectoria en el espacio articular
        pose_stamped = PoseStamped()
        pose_stamped.header.frame_id = 'shoulders_left_link'
        pose_stamped.pose = pose
        resp.pose_stamped = pose_stamped
        resp.graspable = True
        return resp

    else: 
        print("Best_Grasp_Node.-> No possible poses found :'(...................")
        resp.graspable = False
        return resp




def main():
    global listener , ik_srv, marker_pub, marker_array_pub, debug
    debug = True

    print("Node to grab objects based on their orientation by ITZEL..............ʕ•ᴥ•ʔ")

    rospy.init_node("gripper_orientation_for_grasping")
    rospy.Service("/manipulation/get_best_grasp_traj", BestGraspTraj, callback)

    rospy.wait_for_service( '/manipulation/la_ik_trajectory' )
    ik_srv           = rospy.ServiceProxy( '/manipulation/la_ik_trajectory' , InverseKinematicsPose2Traj )
    marker_pub       = rospy.Publisher("/vision/object_recognition/markers",  Marker, queue_size = 10) 
    marker_array_pub = rospy.Publisher("/vision/obj_reco/marker_array",       MarkerArray, queue_size = 10) 

    listener = tf.TransformListener()

    loop = rospy.Rate(30)
    while not rospy.is_shutdown():
        loop.sleep()

if __name__ == '__main__':
    main()