from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import os


def generate_launch_description():

    # Path to RPLidar C1 launch file
    lidar_launch = os.path.expanduser(
        '~/Desktop/slam/install/sllidar_ros2/share/sllidar_ros2/launch/sllidar_c1_launch.py'
    )

    # 1. BNO085 IMU Node
    imu = Node(
        package='imu_node_pkg',
        executable='bno085_node',
        name='bno085_node',
        output='screen'
    )

    # 2. Wheel Odometry Node
    wheel = Node(
        package='wheel_odometry',
        executable='wheel_odom',
        name='wheel_odom',
        output='screen'
    )

    # 3. RPLidar C1 Launch Inclusion
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch)
    )

    # 4. OFFCUP Webcam Node
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

    # 5. Static Transforms
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

    camera_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0.1', '0.0', '0.2', '0', '0', '0', 'base_link', 'camera_link']
    )

    # 6. Robot Localization EKF Node
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

    # 7. Slam Toolbox (Handles 2D Occupancy Grid Mapping -> /map)
    #slam = Node(
    #    package='slam_toolbox',
    #    executable='async_slam_toolbox_node',
    #    name='slam_toolbox',
    #    output='screen',
    #    parameters=[
    #        '/home/nagha/Desktop/robot_bringup_ws/src/robot_bringup/config/slam.yaml',
    #        {'use_sim_time': False}
    #    ]
    #)

    # 8. RTAB-Map (Handles visual-lidar loop closures and global graph optimization)
    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        parameters=[{
            'frame_id': 'base_link',
            'subscribe_depth': False,
            'subscribe_rgb': True,
            'subscribe_scan': True,
            'approx_sync': True,
            'wait_imu_to_init': False,
            'Reg/Strategy': '1',
            'Grid/FromDepth': 'false'
        }],
        remappings=[
            ('rgb/image', '/image_raw'),
            ('scan', '/scan'),
            ('odom', '/odometry/filtered')
        ],
        arguments=['--delete_db_on_start']
    )

    # Delayed startup actions to allow drivers and transforms to settle
    #delayed_slam = TimerAction(
    #    period=3.0,
    #    actions=[slam]
    #)

    delayed_rtabmap = TimerAction(
        period=4.0,
        actions=[rtabmap_node]
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
        #delayed_slam,
        delayed_rtabmap
    ])
