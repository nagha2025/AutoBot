#!/usr/bin/env python3

import math
import lgpio
import rclpy

from rclpy.node import Node
from nav_msgs.msg import Odometry


class WheelOdometry(Node):

    def __init__(self):
        super().__init__('wheel_odometry')

        # ==================================================
        # Robot Parameters
        # ==================================================
        self.ticks_per_rev = 8            # adjust after calibration
        self.wheel_radius = 0.0325        # meters (65 mm wheel)
        self.wheel_base = 0.14            # meters (14 cm actual)

        # ==================================================
        # GPIO
        # ==================================================
        self.gpio_chip = 4

        self.encoders = {
            "FL": {"A": 25, "B": 24},
            "FR": {"A": 5,  "B": 6},
            "RL": {"A": 26, "B": 16},
            "RR": {"A": 17, "B": 27},
        }

        # ==================================================
        # State
        # ==================================================
        self.counts = {
            "FL": 0,
            "FR": 0,
            "RL": 0,
            "RR": 0
        }

        self.prev_state = {}

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        self.last_left = 0.0
        self.last_right = 0.0

        self.last_time = self.get_clock().now()

        # ==================================================
        # ROS
        # ==================================================
        self.odom_pub = self.create_publisher(Odometry, '/odom_raw', 30)

        # ==================================================
        # GPIO Init
        # ==================================================
        self.h = lgpio.gpiochip_open(self.gpio_chip)

        for name, pins in self.encoders.items():
            lgpio.gpio_claim_input(self.h, pins["A"], lgpio.SET_PULL_UP)
            lgpio.gpio_claim_input(self.h, pins["B"], lgpio.SET_PULL_UP)

            a = lgpio.gpio_read(self.h, pins["A"])
            b = lgpio.gpio_read(self.h, pins["B"])
            self.prev_state[name] = (a << 1) | b

        # ==================================================
        # Timer
        # ==================================================
        self.timer = self.create_timer(0.01, self.update)   # 100 Hz

        self.get_logger().info("Quadrature wheel odometry started.")

    # ======================================================
    # Quadrature decode table
    # ======================================================
    def quad_update(self, name):

        pins = self.encoders[name]

        a = lgpio.gpio_read(self.h, pins["A"])
        b = lgpio.gpio_read(self.h, pins["B"])

        new_state = (a << 1) | b
        old_state = self.prev_state[name]

        if new_state == old_state:
            return

        transition = (old_state << 2) | new_state

        forward = [0b0001, 0b0111, 0b1110, 0b1000]
        reverse = [0b0010, 0b0100, 0b1101, 0b1011]

        if transition in forward:
            self.counts[name] += 1
        elif transition in reverse:
            self.counts[name] -= 1

        self.prev_state[name] = new_state

    # ======================================================
    def ticks_to_meters(self, ticks):
        return (2.0 * math.pi * self.wheel_radius) * (ticks / self.ticks_per_rev)

    # ======================================================
    def update(self):

        # ---------------------------------------------
        # Read all encoders
        # ---------------------------------------------
        for name in self.encoders.keys():
            self.quad_update(name)

        # ---------------------------------------------
        # Time
        # ---------------------------------------------
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now

        if dt <= 0.0:
            return

        # ---------------------------------------------
        # Average left / right side
        # ---------------------------------------------
        left_ticks = (self.counts["FL"] + self.counts["RL"]) / 2.0
        right_ticks = -(self.counts["FR"] + self.counts["RR"]) / 2.0

        dl_ticks = left_ticks - self.last_left
        dr_ticks = right_ticks - self.last_right

        self.last_left = left_ticks
        self.last_right = right_ticks

        # ---------------------------------------------
        # Convert to meters
        # ---------------------------------------------
        dl = self.ticks_to_meters(dl_ticks)
        dr = self.ticks_to_meters(dr_ticks)

        # If one side reversed physically, uncomment:
        # dr = -dr

        # ---------------------------------------------
        # Differential drive kinematics
        # ---------------------------------------------
        ds = (dl + dr) / 2.0
        dtheta = (dr - dl) / self.wheel_base

        self.x += ds * math.cos(self.theta + dtheta / 2.0)
        self.y += ds * math.sin(self.theta + dtheta / 2.0)
        self.theta += dtheta

        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        vx = ds / dt
        vth = dtheta / dt

        # ---------------------------------------------
        # Quaternion
        # ---------------------------------------------
        qz = math.sin(self.theta / 2.0)
        qw = math.cos(self.theta / 2.0)

        # ---------------------------------------------
        # Publish Odometry Topic ONLY
        # EKF should publish TF
        # ---------------------------------------------
        odom = Odometry()

        odom.header.stamp = now.to_msg()
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"

        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0

        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw

        odom.twist.twist.linear.x = vx
        odom.twist.twist.angular.z = vth

        odom.pose.covariance = [
            0.05,0,0,0,0,0,
            0,0.05,0,0,0,0,
            0,0,99999,0,0,0,
            0,0,0,99999,0,0,
            0,0,0,0,99999,0,
            0,0,0,0,0,0.1
        ]

        odom.twist.covariance = [
            0.05,0,0,0,0,0,
            0,0.05,0,0,0,0,
            0,0,99999,0,0,0,
            0,0,0,99999,0,0,
            0,0,0,0,99999,0,
            0,0,0,0,0,0.1
        ]

        self.odom_pub.publish(odom)

    # ======================================================
    def destroy_node(self):
        try:
            lgpio.gpiochip_close(self.h)
        except:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = WheelOdometry()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
