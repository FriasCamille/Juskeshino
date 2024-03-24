import rospy
from std_msgs.msg import *
from hri_msgs.msg import *
from sound_play.msg import SoundRequest

class JuskeshinoHRI:
    def setNodeHandle():
        print("JuskeshinoHRI.->Setting ros node...")
        rospy.Subscriber("/hri/sp_rec/recognized", RecognizedSpeech, JuskeshinoHRI.callbackRecognizedSpeech)
        JuskeshinoHRI.pubSoundRequest    = rospy.Publisher("/hri/speech_generator", SoundRequest, queue_size=10)
        JuskeshinoHRI.pubLegFinderEnable = rospy.Publisher("/hri/leg_finder/enable", Bool, queue_size=10)
        JuskeshinoHRI.pubHFollowEnable   = rospy.Publisher("/hri/human_following/enable", Bool, queue_size=10)
        
        JuskeshinoHRI.recognizedSpeech = RecognizedSpeech()
        loop = rospy.Rate(10)
        counter = 3
        while not rospy.is_shutdown() and counter > 0:
            counter-=1
            loop.sleep()
        return True

    def callbackRecognizedSpeech(msg):
        JuskeshinoHRI.recognizedSpeech = msg

    def getLastRecognizedSentence():
        if len(JuskeshinoHRI.recognizedSpeech.hypothesis) < 1:
            return None
        rec = JuskeshinoHRI.recognizedSpeech.hypothesis[0]
        JuskeshinoHRI.recognizedSpeech.hypothesis = tuple([])
        JuskeshinoHRI.recognizedSpeech.confidences = tuple([])
        return rec

    def waitForNewSentence(timeout):
        attempts = int(timeout/0.1)
        loop = rospy.Rate(10)
        JuskeshinoHRI.recognizedSpeech.hypothesis = tuple([])
        JuskeshinoHRI.recognizedSpeech.confidences = tuple([])
        while (not rospy.is_shutdown() and attempts > 0):
            rec = JuskeshinoHRI.getLastRecognizedSentence()
            print("************************************", rec)
            if rec is not None:
                return rec
            loop.sleep()
        return None

    def say(text, voice="voice_cmu_us_slt_arctic_hts"):
        msg = SoundRequest()
        msg.sound   = -3
        msg.command = 1
        msg.volume  = 1.0
        msg.arg2    = voice
        msg.arg     = text
        JuskeshinoHRI.pubSoundRequest.publish(msg)
        rospy.sleep(0.09*len(text))

    def enableHumanFollowing(enable):
        msg = Bool()
        msg.data = enable
        JuskeshinoHRI.pubLegFinderEnable.publish(msg)
        JuskeshinoHRI.pubHFollowEnable.publish(msg)

        
