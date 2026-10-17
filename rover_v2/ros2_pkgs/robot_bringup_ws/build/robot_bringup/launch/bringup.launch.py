from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

import os


def generate_launch_description():

    lidar_launch = os.path.expanduser(
        '~/Desktop/slam/install/sllidar_ros2/share/sllidar_ros2/launch/sllidar_c1_launch.py'
    )

    imu = Node(
        package='imu_node_pkg',
        executable='bno085_node',
        name='bno085_node',
        output='screen'
    )

    wheel = Node(
        package='wheel_odometry',
        executable='wheel_odom',
        name='wheel_odom',
        output='screen'
    )

    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch)
    )

    # OFFCUP Webcam Node
    webcam = Node(
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name='v4l2_camera',
        output='screen',
        parameters=[{
            'video_device': '/dev/video0',
            'image_size': [640, 480],
            'frame_rate': 30.0,
            'camera_frame_id': 'camera_link'
        }]
    )

    imu_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0.05', '0', '0', '0', 'base_link', 'imu_link']
    )

    laser_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0.18', '0', '0.12', '0', '0', '0', 'base_link', 'laser']
    )

    # Camera Static Transform (adjust x, y, z, roll, pitch, yaw relative to base_link)
    camera_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0.1', '0.0', '0.2', '0', '0', '0', 'base_link', 'camera_link']
    )

    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[
            '/home/nagha/Desktop/robot_bringup_ws/src/robot_bringup/config/ekf.yaml',
            {'use_sim_time': False}
        ]
    )

    slam = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            '/home/nagha/Desktop/robot_bringup_ws/src/robot_bringup/config/slam.yaml',
            {'use_sim_time': False}
        ]
    )

    delayed_slam = TimerAction(
        period=3.0,
        actions=[slam]
    )

    return LaunchDescription([
        imu,
        wheel,
        lidar,
        webcam,
        imu_tf,
        laser_tf,
        camera_tf,
        ekf,
        delayed_slam
    ])
