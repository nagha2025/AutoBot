#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import board
import busio
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR

class BNO085Node(Node):
    def __init__(self):
        super().__init__('bno085_node')
        self.publisher_ = self.create_publisher(Imu, '/imu/data', 30)
        
        # Initialize I2C and BNO085
        i2c = busio.I2C(board.SCL, board.SDA)
        self.bno = BNO08X_I2C(i2c)
        
        # Enable rotation vector report for orientation quaternion
        self.bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)
        
        self.timer = self.create_timer(0.033, self.publish_imu) # ~30 Hz
        self.get_logger().info("BNO085 IMU node started, publishing to /imu/data.")

    def publish_imu(self):
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imu_link"
        
        # Read quaternion (i, j, k, real)
        quat = self.bno.quaternion
        if quat is not None:
            msg.orientation.x = float(quat[0])
            msg.orientation.y = float(quat[1])
            msg.orientation.z = float(quat[2])
            msg.orientation.w = float(quat[3])
            
            # Standard orientation covariance
            msg.orientation_covariance[0] = 0.01
            msg.orientation_covariance[4] = 0.01
            msg.orientation_covariance[8] = 0.01

            self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = BNO085Node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()

if __name__ == '__main__':
    main()
