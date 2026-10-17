import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/nagha/Desktop/bno085_ws/install/imu_node_pkg'
