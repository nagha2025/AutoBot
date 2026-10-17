import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/nagha/Desktop/odom/ros_ws/install/wheel_odometry'
