#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
import math

class FakeOdom(Node):

    def __init__(self):
        super().__init__('fake_odom')
        self.br = TransformBroadcaster(self)
        self.timer = self.create_timer(0.1, self.publish_tf)
        self.x = 0.0
        self.get_logger().info("Fake translation odometry started")

    def publish_tf(self):

        now = self.get_clock().now().to_msg()

        # --- odom -> base_link ---
        t1 = TransformStamped()
        t1.header.stamp = now
        t1.header.frame_id = 'odom'
        t1.child_frame_id = 'base_footprint'

        self.x += 0.001

        t1.transform.translation.x = self.x
        t1.transform.translation.y = 0.0
        t1.transform.translation.z = 0.0
        t1.transform.rotation.x = 0.0
        t1.transform.rotation.y = 0.0
        t1.transform.rotation.w = 1.0

        self.br.sendTransform(t1)

        # --- base_link -> laser (dynamic, real timestamp) ---
        t2 = TransformStamped()
        t2.header.stamp = now
        t2.header.frame_id = 'base_footprint'
        t2.child_frame_id = 'laser'

        t2.transform.translation.x = 0.0
        t2.transform.translation.y = 0.0
        t2.transform.translation.z = 0.0
        t2.transform.rotation.x = 0.0
        t2.transform.rotation.y = 0.0
        t2.transform.rotation.z = 0.0
        t2.transform.rotation.w = 1.0

        self.br.sendTransform(t2)


def main():
    rclpy.init()
    node = FakeOdom()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
