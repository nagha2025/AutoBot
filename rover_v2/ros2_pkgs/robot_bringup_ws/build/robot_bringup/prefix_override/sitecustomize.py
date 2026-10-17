import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/nagha/Desktop/robot_bringup_ws/install/robot_bringup'
