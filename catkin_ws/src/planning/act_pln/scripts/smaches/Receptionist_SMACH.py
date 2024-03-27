#!/usr/bin/env python3
from smach_utils_justina import *
# from smach_utils_receptionist import *

##### Define state INITIAL #####

# --------------------------------------------------
camera_enable = False
# TODO: clear print attempts

class Initial(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succ', 'failed'])
        self.tries = 0

    def execute(self, userdata):
        print('\n> STATE <: INITIAL')
        self.tries += 1
        print(f'Try {self.tries} of 5 attempts')

        party.clean_knowledge(host_name="John", host_location="Place_1")
        places_2_tf()

        # -----INIT GRAMMAR FOR VOSK
        # -----Use with get_keywords_speech()
        # -----------SPEECH REC
        drinks = ['coke','juice','milk', 'water', 'soda', 'wine', 
                  'i want a', 'i would like a', 'tea', 'icedtea', 'cola', 'redwine', 'orangejuice', 'tropicaljuice']
       
        names = [' my name is' , 'i am','adel', 'angel', 'axel', 
                 'charlie', 'jane', 'john', 'jules', 'morgan', 'paris', 'robin', 'simone', 'jack']
        confirmation = ['yes','no', 'robot yes', 'robot no','not','now','nope','yeah']                     
        gram = drinks + names + confirmation   

        if self.tries == 1:
            # set_grammar(gram)  ##PRESET DRINKS  # TODO: fix
            print("drinks:")
            print(drinks)
            print("-->")
            return 'succ'
        elif self.tries == 3:
            return 'tries'

        

# --------------------------------------------------

class Wait_push_hand(smach.State):
    pass

# --------------------------------------------------


class Wait_door_opened(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succ', 'failed'])
        self.tries = 0

    def execute(self, userdata):
        self.tries += 1
        if self.tries == 1:
            print("\n")
            rospy.logwarn('--> STATE <: Wait for door to be opened')
            print('Waiting for door to be opened')
            voice.talk('I am ready for receptionist task.')        
        print(f'Try {self.tries} of 4 attempts')

        # if self.tries == 100:
        #     return 'tries'
        voice.talk('I am waiting for the door to be opened')
        rospy.sleep(3.0)

        msg = rospy.wait_for_message('/hardware/scan', LaserScan)
        if np.mean(msg.ranges[(int)(len(msg.ranges)*0.5 - 10):(int)(len(msg.ranges)*0.5 + 10)]) < 1.0:
            return 'failed'  # DOOR
        self.tries = 0
        return 'succ'


class Goto_door(smach.State):  # ADD KNONW LOCATION DOOR
    def __init__(self):
        smach.State.__init__(self, outcomes=['succ', 'failed'])  # TODO: restore tries?
        self.tries = 0

    def execute(self, userdata):
        self.tries += 1
        if self.tries == 1:
            print("\n")
            rospy.logwarn('--> STATE <: Navigate to Door')
            print("Navigating to, door")
            voice.talk('Navigating to, door')

        print(f'Try {self.tries} of 3 attempts')
        if self.tries == 3:  # TODO: Ensure are close to door
            return 'succ'

        res = omni_base.move_base(known_location='door')
        print(res)

        if res:
            self.tries = 0
            return 'succ'
        else:
            rospy.logerr('Navigation Failed, retrying')
            voice.talk('Navigation Failed, retrying')
            return 'failed'

# --------------------------------------------------
class Scan_face(smach.State):
    def __init__(self):
        smach.State.__init__(self, 
                             outcomes = ['succ', 'failed'], 
                             output_keys = ['name', 'face_img'])
        self.tries = 0

    def execute(self, userdata):
        global camera_enable

        self.tries += 1
        if self.tries == 1:
            print("\n")
            rospy.logwarn('--> STATE <: Scan face')

        head.set_joint_values([0.0, -0.1])
        print('Scanning for faces, look at me, please')
        voice.talk('Scanning for faces, look at me, please')
        
        # For simulation use camera_enable = True
        res, userdata.face_img = wait_for_face(lap_camera=camera_enable)  # default 10 secs
        #rospy.sleep(0.7)
        if res != None:
            userdata.name = res.Ids.ids
            return 'succ'
        else:
            return 'failed'

# Decide face STATE: Decide if the new guest is known, unknown or can't be decided

class Decide_face(smach.State):
    def __init__(self):
        smach.State.__init__(self, 
                             outcomes=['succ', 'failed', 'unknown'], 
                             input_keys=['name', 'face_img'], 
                             output_keys=['name', 'face_img'])
        self.tries = 0
    def execute(self, userdata):
        print("\n")
        rospy.logwarn('--> STATE <: Decide face')

        if userdata.name == 'NO_FACE':
            print('I did not see you, I will try again')
            voice.talk('I did not see you, I will try again')
            return 'failed'

        elif userdata.name == 'unknown':
            print('I believe we have not met.')
            voice.talk('I believe we have not met.')
            return 'unknown'

        else:
            print(f'I found you, I Think you are, {userdata.name}.')
            print('Is it correct?')
            voice.talk(f'I found you, I Think you are, {userdata.name}.')
            voice.talk('Is it correct?')
            #rospy.sleep(2.5)
            confirmation = get_keywords_speech(10)
            print(confirmation)

            if confirmation not in ['yes', 'jack', 'juice', 'Justina yes', 'yeah']:
                return 'unknown'
            elif confirmation == "timeout":
                print('I could not hear you, lets try again, please speak louder.')
                voice.talk('I could not hear you, lets try again, please speak louder.')
                return "failed"
            else:
                party.add_guest(userdata.name)
                return 'succ'

# --------------------------------------------------


class New_face(smach.State):
    def __init__(self):
        smach.State.__init__(self, 
                             outcomes=['succ', 'failed'],
                             input_keys=['name', 'face_img'],
                             output_keys=['name', 'face_img'])
        #self.new_name = ''
        #self.num_faces = 0
        self.tries = 0

    def execute(self, userdata):
        self.tries += 1
        if self.tries == 1:
            print("\n")
            rospy.logwarn('--> STATE <: new face')

        #If name is not recognized 3 times, guest will be registered as a "someone"
        if self.tries == 3:
            print("I didn't undestand your name, lets continue")
            voice.talk ('I didnt undestand your name, lets continue')
            userdata.name = 'someone'
            train_face(userdata.face_img, userdata.name)
            party.add_guest(userdata.name)
            self.tries = 0
            return 'succ'
        
        #Asking for name
        print('Please, tell me your name')
        voice.talk('Please, tell me your name')
        #rospy.sleep(1.0)
        speech = get_keywords_speech(10)
        # in case thinks like I am , my name is . etc
        if len(speech.split(' ')) > 1: 
            name = (speech.split(' ')[-1])
        else: 
            name = speech

        if userdata.name == 'timeout':
            print('Please repeat it and speak louder.')
            voice.talk('Please repeat it and speak louder.')
            return 'failed'

        print(f'Is {name} your name?')
        voice.talk(f'Is {name} your name?')
        #rospy.sleep(2.0)
        confirmation = get_keywords_speech(10)
        print (confirmation)

        confirmation = confirmation.split(' ')
        confirm = match_speech(confirmation, ['yes','yeah','jack','juice'])
        if confirm:
            userdata.name = name
            print(f'Nice to Meet You {userdata.name}')
            voice.talk (f'Nice to Meet You {userdata.name}')
            party.add_guest(userdata.name)
            train_face(userdata.face_img, userdata.name)
            self.tries = 0
            return 'succ'
        else:
            print('lets try again')
            voice.talk('lets try again')
            return 'failed'

# --------------------------------------------------


class Get_drink(smach.State):
    def __init__(self):
        smach.State.__init__(self, 
                             outcomes=['succ', 'failed'],
                             input_keys=['name', 'face_img'])
        #self.new_name = ''
        #self.num_faces = 0
        self.tries = 0

    def execute(self, userdata):
        self.tries += 1
        if self.tries == 1:
            print("\n")
            rospy.logwarn('--> STATE <: get drink')
            # TODO: implement
            #analyze_face_background(userdata.face_img, userdata.name)#userdata.name)
            pass
        elif self.tries == 3:
            voice.talk ('I am having trouble understanding you, lets keep going')
            drink = 'something'
            self.tries=0
            party.add_guest_drink(drink)
            #analyze_face_background(userdata.face_img, userdata.name)
            return 'succ'
        
        #Asking for drink
        print('What would you like to drink?')
        voice.talk('What would you like to drink?')
        #rospy.sleep(2.0)
        drink = get_keywords_speech(10)

        if len(drink.split(' '))>1: drink=(drink.split(' ')[-1])
        print(drink)
        rospy.sleep(0.5)

        if drink=='timeout':
            print("Sorry, couldn't hear you. Please speak louder.")
            voice.talk("Sorry, couldn't hear you. Please speak louder.")
            return 'failed'
        print(f'Did you say {drink}?')
        voice.talk(f'Did you say {drink}?')

        #rospy.sleep(2.5)
        confirmation = get_keywords_speech(10)
        confirmation = confirmation.split(' ')
        confirm = match_speech(confirmation, ['yes', 'yeah', 'jack', 'juice'])
        if not confirm: 
            return 'failed' 

        party.add_guest_drink(drink)
        print("Nice")
        voice.talk("Nice")
        self.tries = 0
        return 'succ'

# --------------------------------------------------


class Lead_to_living_room(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succ', 'failed'])
        self.tries = 0

    def execute(self, userdata):
        self.tries += 1
        print('Try', self.tries, 'of 3 attempts')
        if self.tries == 1:
            print("\n")
            rospy.logwarn('--> STATE <: navigate to known location')  # TODO: print location

        # _,guest_name = get_waiting_guests()   #KNOWLEDGE UTILS 
        print(f'{party.get_active_guest_name()}... I will lead you to the living room, please follow me')
        voice.talk(f'{party.get_active_guest_name()}... I will lead you to the living room, please follow me')
        print('Navigating to ,living room')
        voice.talk('Navigating to ,living room')

        res = omni_base.move_base(known_location='living_room')
        if res:
            self.tries = 0
            return 'succ'
        else:
            rospy.logerr('Navigation Failed, retrying')
            voice.talk('Navigation Failed, retrying')
            return 'failed'

# --------------------------------------------------


class Find_sitting_place(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succ', 'failed'])
        self.tries = 0
    def execute(self, userdata):
        global camera_enable
        self.tries += 1
        if self.tries == 1:
            print("\n")
            rospy.logwarn('--> STATE <: looking for a place to sit')

        print('Try', self.tries, 'of 3 attempts')

        print("I am looking for a place to sit")
        voice.talk('I am looking for a place to sit')
        isPlace, place = party.get_active_seat()
        # TDO: delete...
        # isLocation, loc = party.get_active_seat_location()
        # if isLocation:
        #     #omni_base.move_base(*loc)
        #     pass
        # else:
        #     voice.talk('Sorry, there is no more places to sit')
        #     return 'succ'

        if isPlace:
            tf_name = place.replace('_', '_face')
            #head.to_tf(tf_name)  # TODO: implement

        #commented detect human  # TODO: delete?
        #res = detect_human_to_tf()  # TODO: delete?
        print('I will check if this place is empty')
        voice.talk('I will check if this place is empty')
        
        # For simulation use camera_enable = True
        res , _ = wait_for_face(lap_camera=camera_enable)  # seconds
        if res == None:
            print("Place is: ", place)
            guest = party.get_active_guest_name()
            #.turn_base_gaze(tf = place, to_gaze = 'arm_flex_link')  # TODO: implement
            head.set_named_target('neutral')
            rospy.sleep(0.8)

            #brazo.set_named_target('neutral')  # TODO: implement
            print(f'{guest}, Here is a place to sit')
            voice.talk(f'{guest}, Here is a place to sit')


            party.seat_confirmation()
            self.tries = 0 
            return 'succ'

        else:
            occupant_name = res.Ids.ids
            if occupant_name == 'unknown':
                occupant_name = 'someone'
            party.seat_confirmation(occupant_name)
            print(f'I am sorry, here is {occupant_name}, I will find another place for you')
            voice.talk(f'I am sorry, here is {occupant_name}, I will find another place for you')
            return 'failed'

# --------------------------------------------------

class Find_host_alternative(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes= ['succ', 'failed'],
                             output_keys=['name_like_host'])
        self.tries = 0
    def execute(self, userdata):
        global camera_enable
        self.tries += 1

        host_name = ""
        host_loc = ""
        dont_compare = False

        # First try: looks for the real host
        # Next tries: looks for anyone
        if self.tries == 1:
            print("\n")
            rospy.logwarn('--> STATE <: find host alternative')
            host_name, host_loc = party.get_host_info()
            if host_loc == 'None':
                return 'failed'
        else:
            seats = party.get_guests_seat_assignments()
            print("seats: ", seats)

            for place, guest in seats.items():
                if guest != party.get_active_guest():
                    host_loc = place
                    dont_compare = True
                    break
        
        #print("host location is: ", host_loc)
        #print("host name is: ", host_name)
        print(f'looking for host on: {host_loc}')
        voice.talk(f'looking for host on: {host_loc}')
        tf_host = host_loc.replace('_', '_face')
        #head.to_tf(tf_host)  # TODO: implement

        # For simulation use camera_enable = True
        res, _ = wait_for_face(lap_camera=camera_enable)
        if res is not None:
            person_name = res.Ids.ids
            if (person_name == host_name) or dont_compare:
                userdata.name_like_host = person_name
                return 'succ'
            else:
                return 'failed'
        else:
            return 'failed'

# --------------------------------------------------


class Introduce_guest(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succ', 'failed', 'tries'],
                             input_keys=['name_like_host'])
        self.tries = 0

    def execute(self, userdata):
        self.tries += 1
        if self.tries == 1:
            print("\n")
            rospy.logwarn('--> STATE <: find host')

        print('Try', self.tries, 'of 3 attempts')
        print(f'Host like name is {userdata.name_like_host}')
        voice.talk(f'Host like name is {userdata.name_like_host}')

        active_guest = party.get_active_guest_name()
        justina_line = party.get_active_guest_description()                    
        drink = party.get_active_guest_drink()

        if drink == 'something':
            drink_line = ""
        else:
            drink_line = f'And likes {drink}'

        if justina_line != 'None':
            print("Description found")
            speech = f'{userdata.name_like_host}, {justina_line}, {drink_line}'
            timeout = 14.0
        else:
            print('No description found')
            speech = f'{userdata.name_like_host}, {active_guest} has arrived, {drink_line}'
            timeout = 7.0

        print(speech)
        voice.talk(speech, timeout)
        
        if self.tries < 3:
            return 'succ'
        else:
            print('Task completed, thanks for watching')
            voice.talk("Task completed, thanks for watching")
            return 'tries'



# --------------------------------------------------
# Entry point
if __name__ == '__main__':
    print("Justina STATE MACHINE...")

    # State machine, final state "END"
    sm = smach.StateMachine(outcomes=['END'])

    # sm.userdata.clear = False
    sis = smach_ros.IntrospectionServer(
        'SMACH_VIEW_SERVER', sm, '/SM_RECEPTIONIST')
    sis.start()

    with sm:
        # State machine for Receptionist task

        # Initial states routine
        smach.StateMachine.add("INITIAL", Initial(),              
                               transitions={'failed': 'INITIAL', 'succ': 'WAIT_DOOR_OPENED'})
        # smach.StateMachine.add("WAIT_PUSH_HAND", Wait_push_hand(),       
        #                        transitions={'failed': 'WAIT_PUSH_HAND', 'succ': 'GOTO_DOOR'})
        smach.StateMachine.add("WAIT_DOOR_OPENED", Wait_door_opened(),     
                               transitions={'failed': 'WAIT_DOOR_OPENED', 'succ': 'GOTO_DOOR'})
        smach.StateMachine.add("GOTO_DOOR", Goto_door(),            
                               transitions={'failed': 'GOTO_DOOR', 'succ': 'SCAN_FACE'})
        # Guest recognition states
        smach.StateMachine.add("SCAN_FACE", Scan_face(),    
                               transitions={'failed': 'SCAN_FACE', 'succ': 'DECIDE_FACE'})
        smach.StateMachine.add("DECIDE_FACE", Decide_face(),
                               transitions={'failed': 'SCAN_FACE', 'succ': 'GET_DRINK', 'unknown': 'NEW_FACE'})
        smach.StateMachine.add("NEW_FACE", New_face(),     
                               transitions={'failed': 'NEW_FACE', 'succ': 'GET_DRINK'})
        smach.StateMachine.add("GET_DRINK", Get_drink(),    
                               transitions={'failed': 'GET_DRINK', 'succ': 'LEAD_TO_LIVING_ROOM'})

        # Final states
        smach.StateMachine.add("LEAD_TO_LIVING_ROOM", Lead_to_living_room(),  
                               transitions={'failed': 'LEAD_TO_LIVING_ROOM', 'succ': 'FIND_SITTING_PLACE'})
        smach.StateMachine.add("FIND_SITTING_PLACE", Find_sitting_place(),
                               transitions={'failed': 'FIND_SITTING_PLACE', 'succ': 'FIND_HOST'})
        smach.StateMachine.add("FIND_HOST", Find_host_alternative(),
                               transitions={'failed': 'FIND_HOST', 'succ':'INTRODUCE_GUEST'})
        smach.StateMachine.add("INTRODUCE_GUEST", Introduce_guest(),
                               transitions={'failed': 'INTRODUCE_GUEST', 'succ':'GOTO_DOOR', 'tries':'END'})


    outcome = sm.execute()