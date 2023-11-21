#!/usr/bin/env python3

import rospy
import math
import numpy as np
import tf.transformations as tft
import tf2_ros
import tf
from geometry_msgs.msg import PoseStamped, Point, PointStamped, Pose
from vision_msgs.srv import *
from manip_msgs.srv import *
from visualization_msgs.msg import Marker, MarkerArray
import geometry_msgs.msg

MAXIMUM_GRIP_LENGTH = 0.17


def pose_actual_to_pose_target(pose, f_actual, f_target):
    global listener
    poseStamped_msg = PoseStamped()  
    poseStamped_msg.header.frame_id = f_actual   # frame de origen
    poseStamped_msg.header.stamp = rospy.Time(0)  # la ultima transformacion
    poseStamped_msg.pose = pose
    new_poseStamped = listener.transformPose(f_target, poseStamped_msg)
    new_pose = new_poseStamped.pose
    return new_pose


def points_actual_to_points_target(point_in, f_actual, f_target):
    global listener
    point_msg = PointStamped()  
    point_msg.header.frame_id = f_actual   # frame de origen
    point_msg.header.stamp = rospy.Time(0)  # la ultima transformacion
    point_msg.point.x = point_in[0]
    point_msg.point.y = point_in[1]
    point_msg.point.z = point_in[2]
    point_target_frame = listener.transformPoint(f_target, point_msg)
    new_point = point_target_frame.point
    return [ new_point.x , new_point.y , new_point.z ]


def flat_objects_grip(obj_pose, size_obj):
    grip_point = []     # se define el punto de agarre
    # Si 1pca < 0.1 m : small_obj()
    # si no:            top_grip()
    return 


def top_grip(grip_point, obj_pose, ):
        obj_state = "horizontal"
        print("Candidatos 1")
        pose_list1 = generates_candidates(grip_point , obj_pose, "P", obj_state ,  'object', step = -10, num_candidates = 5)
        grip_point = [obj_pose.position.x , obj_pose.position.y, obj_pose.position.z]
        # Segunda lista de candidatos******************************************************************************
        print("Candidatos 2")
        pose_list2 = generates_candidates(grip_point , obj_pose, "P", obj_state ,  'object', step = 10, num_candidates = 5)
        # Tercera lista de candidatos.................................
        obj_pose_frame_object = pose_actual_to_pose_target(obj_pose , 'base_link', 'object') # Transforma pose en frame 'object' para generar candidatos
        
        R, P, Y = tft.euler_from_quaternion([obj_pose_frame_object.orientation.x ,  # pose expresada en RPY para realizar rotaciones
                                             obj_pose_frame_object.orientation.y ,
                                             obj_pose_frame_object.orientation.z, 
                                             obj_pose_frame_object.orientation.w])
        
        Y = Y + np.deg2rad(180) # Realiza un yaw de 180 grados 
        q_gripper = tft.quaternion_from_euler(R,P,Y,'sxyz')  # Pose en frame 'object' cuaterniones
        obj_pose_frame_object.orientation.x = q_gripper[0]
        obj_pose_frame_object.orientation.y = q_gripper[1]
        obj_pose_frame_object.orientation.z = q_gripper[2]
        obj_pose_frame_object.orientation.w = q_gripper[3]

        grip_point = [obj_pose.position.x , obj_pose.position.y, obj_pose.position.z]
        obj_pose_3 = pose_actual_to_pose_target(obj_pose_frame_object , 'object', 'base_link')

        if debug:
            broadcaster_frame_object('base_link', 'test_prism h3', obj_pose_3)  # emite la pose en 'base_link'
            rospy.sleep(1.0)
        
        #grip_point = [obj_pose_3.position.x, obj_pose_3.position.y, obj_pose_3.position.z]
        print("Candidatos 3")
        pose_list3 = generates_candidates(grip_point, obj_pose_3 , "P", obj_state , 'object', step = -10, num_candidates = 5)
        grip_point = [obj_pose.position.x , obj_pose.position.y, obj_pose.position.z]
        print("Candidatos 4")
        pose_list4 = generates_candidates(grip_point, obj_pose_3 , "P", obj_state , 'object', step = 10, num_candidates = 5)

        return pose_list2 + pose_list1 + pose_list3 + pose_list4



def generates_candidates(grip_point , obj_pose, rotacion, obj_state , object_frame, step, num_candidates):    # Cambiar nombre por generates_candidates
    """
        grip_point:     Vector que contiene  el punto origen de los sistemas candidatos, entra en el sistema base_link.
        obj_pose:       Orientacion del objeto en msg Pose en frame 'base_link', expresado en cuaterniones.
        rotacion:       Es un string: roll , pitch o yaw: 'R', 'P', 'Y', tipo de rotacion a realizar en el object_frame.
        obj_state:      Es un string que  indica si el objeto esta 'horizontal' o 'vertical'.
        object_frame:   Es el frame en el cual se van a generar los candidatos de retorno.
        step:           Grados de distancia entre un candidato y otro, pueden ser negativos o positivos.
        num_candidates: Es la cantidad de candidatos que se desea generar.

        Retorna una lista de poses candidatas expresadas en cuaterniones (msg Pose)
    """
    grasp_candidates_quaternion = []
    candidate_grasp = Pose()
    print("publica punto de agarre ")
    marker_array_publish(grip_point , 'base_link', 0, 7)    # publica el punto de agarre para brazo izquierdo


    if obj_state == "horizontal": grip_point[2] = grip_point[2] + 0.13  # 10 cm por encima del objeto (z_base_link)

    obj_pose_frame_object = pose_actual_to_pose_target(obj_pose , 'base_link', object_frame) # pose en frame 'object'
    
    R, P, Y = tft.euler_from_quaternion([obj_pose_frame_object.orientation.x ,  # pose expresada en RPY
                                             obj_pose_frame_object.orientation.y ,
                                             obj_pose_frame_object.orientation.z, 
                                             obj_pose_frame_object.orientation.w])
    
    for j in range(num_candidates):      # genera candidatos
        q_gripper = tft.quaternion_from_euler(R,P,Y,'sxyz')  # Pose en frame 'object' cuaterniones
        obj_pose_frame_object.orientation.x = q_gripper[0]
        obj_pose_frame_object.orientation.y = q_gripper[1]
        obj_pose_frame_object.orientation.z = q_gripper[2]
        obj_pose_frame_object.orientation.w = q_gripper[3]
        if rotacion == "P": 
            P = P + np.deg2rad(step) #horizontal grip
            print("Rotacion en Pitch")

        else:
            if rotacion == "R": R = R + np.deg2rad(step)  #vertical grip
            print("Rotacion en Roll")
        # TRANSFORMAR DIRECTAMENTE A LEFT ARM???
        candidate_grasp = pose_actual_to_pose_target(obj_pose_frame_object , object_frame, 'base_link')    # pose en frame 'base_link'
        candidate_grasp.position.x = grip_point[0] 
        candidate_grasp.position.y = grip_point[1] 
        candidate_grasp.position.z = grip_point[2] 
        if debug:
            broadcaster_frame_object('base_link', 'test_candidates'+str(j)+obj_state , candidate_grasp )  # emite la pose en 'base_link'
            rospy.sleep(1.0)
        grasp_candidates_quaternion.append(candidate_grasp )     # guarda el candidato en frame bl

    print("Antes de len................")
    print("len candidates grip box", len(grasp_candidates_quaternion))

    return grasp_candidates_quaternion  # REGRESA A LOS CANDIDATOS EN FRAME BASE_LINK



def grip_rules(obj_pose, type_obj, obj_state, size):
    if (size.z <= MAXIMUM_GRIP_LENGTH) and (size.y <= MAXIMUM_GRIP_LENGTH) and (size.x >= 0.13):
        print("size object < MAX LENGHT GRIP")
        print("The object will be grabbed as Prism..................")
        return prism(obj_pose, obj_state)
    else:
        if size.x < 0.13:
            print("Object too small, superior grip will be made")
            return small_obj(obj_pose, obj_state )
            
        else:
            print("size object > MAX LENGHT GRIP")
            print("The object will be grabbed as Box....................")
            return box(obj_pose, size, obj_state )



def small_obj(obj_pose, obj_state):
    global debug
    print("Small object")
    grip_point = [obj_pose.position.x, obj_pose.position.y, obj_pose.position.z]
    pose_list1 = generates_candidates(grip_point, obj_pose, "P", obj_state, 'object',  step = -14, num_candidates = 7)
    
    # Segunda lista de poses
    obj_pose_frame_object = pose_actual_to_pose_target(obj_pose , 'base_link', 'object') # Transforma pose en frame 'object' para generar candidatos

    R, P, Y = tft.euler_from_quaternion([obj_pose_frame_object.orientation.x ,  # pose expresada en RPY para realizar rotaciones
                                             obj_pose_frame_object.orientation.y ,
                                             obj_pose_frame_object.orientation.z, 
                                             obj_pose_frame_object.orientation.w])
    Y = Y + np.deg2rad(-45) 
    q_gripper = tft.quaternion_from_euler(R,P,Y,'sxyz')  # Pose en frame 'object' cuaterniones
    obj_pose_frame_object.orientation.x = q_gripper[0]
    obj_pose_frame_object.orientation.y = q_gripper[1]
    obj_pose_frame_object.orientation.z = q_gripper[2]
    obj_pose_frame_object.orientation.w = q_gripper[3]

    obj_pose2 = pose_actual_to_pose_target(obj_pose_frame_object , 'object', 'base_link')
    if debug:	
        broadcaster_frame_object('base_link', 'test_small', obj_pose2)  # emite la pose en 'base_link'
        rospy.sleep(1.0)
    grip_point = [obj_pose2.position.x, obj_pose2.position.y, obj_pose2.position.z]

    pose_list2 = generates_candidates(grip_point ,  obj_pose2, "P", obj_state , 'object', step = -13, num_candidates = 6)

    return pose_list1 + pose_list2


def box(obj_pose, size, obj_state):     # obj_pose  esta referenciada a 'base_link'
    global debug

    # HORIZONTAL 1PCA *****************************************************************************************************************************************************************
    if obj_state == 'horizontal':  
        print("Horizontal box")
        # genera punto de agarre superior
        grip_point_top = points_actual_to_points_target([0, 0, size.z/3], 'object', 'base_link')  
        pose_list_1 = top_grip(grip_point_top, obj_pose) 
        # genera punto de agarre lateral
        grip_point_side = points_actual_to_points_target([-size.x/3, 0, 0], 'object', 'base_link') 

        return 

    
    # VERTICAL GRASP *************************************************************************************************************************************************
    else:  # VERTICAL object, lateral grip
        grip_point1 = points_actual_to_points_target([0, 0, size.z/4] , 'object', 'base_link')  # punto lateral en frame object
        poses_list1 = generates_candidates(grip_point1 , obj_pose, "R", obj_state ,'object', step = 10, num_candidates = 5)  

        return poses_list1 # En frame base_link



def prism(obj_pose, obj_state):   
    global listener, debug
    grasp_candidates_quaternion = []
    epsilon = 0.001 # radio de la circunferencia

    obj_centroid = np.asarray([obj_pose.position.x , obj_pose.position.y, obj_pose.position.z]) # origen de la circunferencia
    MT = tft.quaternion_matrix([obj_pose.orientation.x ,obj_pose.orientation.y, obj_pose.orientation.z, obj_pose.orientation.w])
    axis_x_obj = np.asarray( [MT[0,0], MT[1,0], MT[2,0]])   # eje x del objeto vector normal al plano que corta al objet
    
    step_size = np.deg2rad(15)
    range_points = np.deg2rad(300)          # rango dentro del cual se generan los candidatos 360 grados
    num_points = int(range_points / step_size) 
    theta_offset = np.deg2rad(-25)
    theta = theta_offset
    count = 0
    id = 0
    points = []

    axis_x_point = axis_x_obj / np.linalg.norm( (axis_x_obj) )  # solo toma la 1pca para crear frame de objeto

    # HORIZONTAL **************************************************************************************************
    if obj_state == 'horizontal': 
        print("Horizontal grip prism............")  # Agarre horizontal
        grip_point = [obj_pose.position.x , obj_pose.position.y, obj_pose.position.z] 
        return top_grip(grip_point, obj_pose)

    # VERTICAL ***************************************************************************************************    
    else:
        print("Vertical grip.................")
        for i in range( num_points):   # generación de puntos alrededor del objeto
            point = np.asarray([ 0, epsilon*np.sin(theta), epsilon*np.cos(theta)  ])
            point = points_actual_to_points_target(point, 'object', 'base_link')
            points.append(point)
            marker_array_publish(point, 'base_link', count, id)
            count += 1
            id += 1
            theta = theta - step_size 
        print("number of points", len(points))
        j = 0

        for p in points:   # generacion de frames candidatos
            axis_z_point = (p - obj_centroid ) / np.linalg.norm( (p - obj_centroid ) )
            axis_y_point = np.cross(axis_z_point , axis_x_point) / np.linalg.norm( np.cross(axis_z_point , axis_x_point) )
            # los cuaterniones necesarios para generar el frame del gripper
            RM = np.asarray( [axis_x_point, axis_y_point, axis_z_point] ) 
            RM = RM.T
            TM = [[RM[0,0], RM[0,1] , RM[0,2], 0],
                [RM[1,0], RM[1,1] , RM[1,2],   0],
                [RM[2,0], RM[2,1] , RM[2,2],   0], 
                [      0,        0,       0,   1]]
        
            q_gripper = tft.quaternion_from_matrix( TM ) 
            candidate_grasp = Pose()
            candidate_grasp.position.x = p[0] 
            candidate_grasp.position.y = p[1] 
            candidate_grasp.position.z = p[2] 
            candidate_grasp.orientation.x = q_gripper[0]
            candidate_grasp.orientation.y = q_gripper[1]
            candidate_grasp.orientation.z = q_gripper[2]
            candidate_grasp.orientation.w = q_gripper[3]
            grasp_candidates_quaternion.append(candidate_grasp) 
            if debug:
                broadcaster_frame_object('base_link', 'vertical_prism'+str(j) , candidate_grasp )  # emite la pose en 'base_link'
                rospy.sleep(1.0)
            j += 1
        print("number of candidates vertical grip prism", len(grasp_candidates_quaternion))
        return grasp_candidates_quaternion
        


def arow_marker(p_offset, p1, frame_id, ns, id, color):  # P1 y P2
    point0 = Point()
    point0.x = p_offset[0] 
    point0.y = p_offset[1] 
    point0.z = p_offset[2] 
    marker1 = Marker()
    marker1.header.frame_id = frame_id
    marker1.type = Marker.ARROW
    marker1.ns = ns
    marker1.header.stamp = rospy.Time.now()
    marker1.action = marker1.ADD
    marker1.id = id
    # body radius, Head radius, hight head
    marker1.scale.x, marker1.scale.y, marker1.scale.z = 0.009, 0.05, 0.02 
    marker1.color.r , marker1.color.g , marker1.color.b, marker1.color.a = color, 0.0, 100.0, 1.0
    point1 = Point()
    point1.x = p_offset[0] + p1[0]
    point1.y = p_offset[1] + p1[1]
    point1.z = p_offset[2] + p1[2]
    marker1.points = [point0, point1]
    marker_pub.publish(marker1)



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
    print("graficando frames en Rviz..........")



def convert_frame_of_candidates_poses(pose_list_q, o):
    """
        Convierte las poses de entrada que estan respecto de 'base_link' en poses
        con respecto a 'shoulders_left_link' 
        Argumentos de entrada
        pose_list_q: lista de poses candidatas en cuaterniones
        Argumentos de salida
        new_pose_rpy_list: 
    """
    new_pose_q_list = []        # Poses en cuaterniones para 
    new_pose_rpy_list = []      # Poses en RPY para el servicio de cinematica inversa
    for pos in pose_list_q: # para cada candidato de la lista de entrada
        new_pose = pose_actual_to_pose_target(pos, 'base_link' , 'shoulders_left_link')
        new_pose_q_list.append(new_pose)
        # Se extrae la informacion de la posicion del objeto respecto al frame de hombro izqu
        x , y, z = new_pose.position.x , new_pose.position.y , new_pose.position.z
        roll,pitch,yaw = tft.euler_from_quaternion( [new_pose.orientation.x , new_pose.orientation.y , 
                                          new_pose.orientation.z , new_pose.orientation.w ])
        pose_shoulder_frame = np.asarray([x ,y ,z , roll, pitch , yaw])
        new_pose_rpy_list.append(pose_shoulder_frame)
    return new_pose_rpy_list


    
def evaluating_possibility_grip(pose_rpy, pose_quaternion, obj_state):
    """
        Evalua la existencia de los candidatos de agarre en el espacio articular y regresa una trayectoria
        desde la posicion actual del grippe hasta el origen del primer frame candidato aprobado h
    """
    global ik_srv
    print("The object grabbing service was called............")
    ik_msg = InverseKinematicsPose2TrajRequest()
    print("Evaluating the possibility of grip given the position of the object...")
    i = 0
    for pose1 in pose_rpy:  # rellena el mensaje para el servicio IK
        if obj_state == "vertical":
            ik_msg.x = pose1[0] 
            ik_msg.y = pose1[1]
            ik_msg.z = pose1[2]
            ik_msg.roll = pose1[3]
            ik_msg.pitch = pose1[4]
            ik_msg.yaw = pose1[5]
            ik_msg.duration = 4
            ik_msg.time_step = 0.02
            try:
                resp_ik_srv = ik_srv(ik_msg)
                print("Suitable pose for vertical object found.....................")
                return resp_ik_srv.articular_trajectory , pose_quaternion[i] , pose1, True
            except:
                i = i + 1 
                print("Pose no apta........")  
                continue


        else:   # objeto con 1pca horizontal
            ik_msg.x = pose1[0] 
            ik_msg.y = pose1[1]
            ik_msg.z = pose1[2]
            ik_msg.roll = pose1[3]      # (0, -90,0)
            ik_msg.pitch = pose1[4]
            ik_msg.yaw = pose1[5]
            ik_msg.duration = 4
            ik_msg.time_step = 0.02
            try:    # intenta la primera trayectoria
                
                resp_ik_srv = ik_srv(ik_msg)    # Envia al servicio de IK
                print("Suitable pose 1 for horizontal object found.....................")
                #print("ultimo punto de la trayectoria")
                #print(resp_ik_srv.articular_trajectory.points[-1])
                #return resp_ik_srv.articular_trajectory , pose_quaternion[i] , pose1, True
            except:
                print("pose 1 no apta")
                continue
    
            try:
                print("genera una segunda trayectoria para objeto horizontal")
                # el ultimo punto de la 1a trayectoria es el primero de la segunda
                #print("ULTIMO PUNTO DE LA TRAYECTORIA", resp_ik_srv.articular_trajectory.points[-1].positions)
                guess = [resp_ik_srv.articular_trajectory.points[-1].positions[0],
                        resp_ik_srv.articular_trajectory.points[-1].positions[1],
                        resp_ik_srv.articular_trajectory.points[-1].positions[2],
                        resp_ik_srv.articular_trajectory.points[-1].positions[3],
                        resp_ik_srv.articular_trajectory.points[-1].positions[4],
                        resp_ik_srv.articular_trajectory.points[-1].positions[5],
                        resp_ik_srv.articular_trajectory.points[-1].positions[6]]
                    
                # Ultimo punto de la segunda trayectoria
                ik_msg.x = pose1[0] 
                ik_msg.y = pose1[1]
                ik_msg.z = pose1[2] - 0.06
                ik_msg.roll = pose1[3]
                ik_msg.pitch = pose1[4]
                ik_msg.yaw = pose1[5]
                ik_msg.duration = 2
                ik_msg.time_step = 0.02
                ik_msg.initial_guess = guess

                resp_2_ik_srv = ik_srv(ik_msg)    # Envia al servicio de IK
                print("Second trajectory found.....................")
                resp_ik_srv.articular_trajectory.points = resp_ik_srv.articular_trajectory.points + resp_2_ik_srv.articular_trajectory.points
                return resp_ik_srv.articular_trajectory , pose_quaternion[i] , pose1, True
            except:
                i = i + 1 
                print("Pose 2 no apta........")  
                continue
            
    return None, None, None, False



def callback(req):
    global listener #, ik_srv
    resp = BestGraspTrajResponse()              
    obj_state = req.recog_object.object_state    

    print("Position centroid Obj: ")
    print(req.recog_object.pose.position)

    pose_list_quaternion = grip_rules(req.recog_object.pose, req.recog_object.category, obj_state, req.recog_object.size )
    if len( pose_list_quaternion) <= 0:
        print("object is no graspable")
        return resp
    
    candidates_poses_rpy = convert_frame_of_candidates_poses( pose_list_quaternion , obj_state)
    trajectory, pose, rpy_pose, graspable = evaluating_possibility_grip(candidates_poses_rpy ,  pose_list_quaternion , obj_state)
   
    if graspable:
        print("Graficando en RViz pose adecuada para manipulacion de objetos....")
        #broadcaster_frame_object('base_link', 'suitable_pose' , pose)
        rospy.sleep(1.0)
        resp.articular_trajectory = trajectory
        resp.graspable = True
        return resp

    else: 
        print("No possible poses found :'(...................")
        resp.graspable = False
        return resp



def main():
    global listener , ik_srv, marker_pub, marker_array_pub, debug
    debug = True
    print("Node to grab objects based on their orientation by Iby..............ʕ•ᴥ•ʔ")
    rospy.init_node("gripper_orientation_for_grasping")
    rospy.Service("/vision/get_best_grasp_traj", BestGraspTraj, callback)
    listener = tf.TransformListener()
    # se suscribe al servicio /manipulation/ik_trajectory
    rospy.wait_for_service( '/manipulation/la_ik_trajectory' )
    ik_srv = rospy.ServiceProxy( '/manipulation/la_ik_trajectory' , InverseKinematicsPose2Traj )
    marker_pub = rospy.Publisher("/vision/object_recognition/markers", Marker, queue_size = 10) 
    marker_array_pub = rospy.Publisher("/vision/obj_reco/marker_array", MarkerArray, queue_size = 10) 
    
    loop = rospy.Rate(30)
    while not rospy.is_shutdown():
        loop.sleep()

if __name__ == '__main__':
    main()


