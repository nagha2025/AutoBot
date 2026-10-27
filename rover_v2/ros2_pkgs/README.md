# AutoBot ROS 2 Sensor, Odometry, Bringup and SLAM Stack

This README consolidates the setup and operation notes for the AutoBot
ROS 2 packages and drivers:

-   **`imu_node_pkg`** --- BNO085 IMU publisher
-   **`wheel_odometry`** --- wheel-encoder odometry publisher
-   **`robot_bringup`** --- launches sensors, transforms, EKF and the
    selected mapping pipeline
-   **`sllidar_ros2`** --- RPLIDAR C1 ROS 2 driver
-   **SLAM / mapping** --- SLAM Toolbox or RTAB-Map, depending on the
    active launch configuration

The documented platform is **Raspberry Pi 5, Ubuntu 24.04 (Noble), ROS 2
Jazzy**, with the RPLIDAR C1 and BNO085 connected to the robot. The
wheel-odometry node accesses GPIO encoder inputs on the Raspberry Pi
where it runs.

> **Configuration warning:** The saved `bringup.launch.py` currently
> contains legacy webcam settings, hard-coded workspace paths, a
> commented-out SLAM Toolbox node, and an RTAB-Map configuration that
> subscribes to `/image_raw`. AutoBot's RealSense D421 is a depth/stereo
> camera and does not provide a conventional RGB stream. Review the
> camera and RTAB-Map configuration before treating the current launch
> file as a working D421 visual-SLAM launch. The steps below distinguish
> the known configuration from items that must be checked on the
> installed system.

## 1. System overview

  -----------------------------------------------------------------------
  Component               ROS package / node      Main output
  ----------------------- ----------------------- -----------------------
  BNO085 IMU              `imu_node_pkg` /        `/imu/data`
                          `bno085_node`           

  Wheel encoders          `wheel_odometry` /      `/odom_raw`
                          `wheel_odom`            

  State estimation        `robot_localization` /  `/odometry/filtered`
                          `ekf_filter_node`       and the
                                                  `odom → base_link` TF,
                                                  according to EKF
                                                  configuration

  RPLIDAR C1              `sllidar_ros2`          `/scan`

  Static transforms       `tf2_ros`               `/tf_static`

  2D SLAM option          `slam_toolbox`          `/map` and SLAM-related
                                                  topics

  Graph-based mapping     `rtabmap_slam` /        RTAB-Map map/graph
  option                  `rtabmap`               products and, when
                                                  configured, occupancy
                                                  grid

  Camera (legacy launch   `v4l2_camera`           Legacy `/image_raw`
  entry)                                          configuration; verify
                                                  against the current
                                                  camera
  -----------------------------------------------------------------------

The typical data path is:

1.  The IMU publishes inertial data on `/imu/data`.
2.  The wheel odometry node publishes encoder-based estimates on
    `/odom_raw`.
3.  `robot_localization` fuses configured wheel and IMU measurements and
    publishes `/odometry/filtered`.
4.  The RPLIDAR driver publishes laser scans on `/scan`.
5.  A SLAM node consumes the required scan, odometry, TF and (for
    visual/stereo configurations) camera data.

## 2. Prerequisites

-   Ubuntu 24.04 and ROS 2 Jazzy installed.
-   ROS environment sourced in every terminal.
-   BNO085 connected and supported by the installed `imu_node_pkg`
    implementation.
-   Encoder signals wired to the GPIO pins configured in
    `wheel_odometry`.
-   RPLIDAR C1 connected over USB and accessible to the user running the
    driver.
-   Required ROS packages installed: `robot_localization`, `tf2_ros`,
    `slam_toolbox` and/or `rtabmap-ros`, plus the RPLIDAR driver.
-   Python dependencies for the custom nodes installed in the
    environment used to run them.

Source ROS 2 Jazzy:

``` bash
source /opt/ros/jazzy/setup.bash
```

If workspaces are built from source, source each workspace's
`install/setup.bash` after sourcing ROS. Use the actual workspace paths
on the machine; the examples below use the workspace names previously
used for AutoBot.

## 3. Workspace layout

The packages have previously been developed in separate workspaces:

``` text
~/Desktop/bno085_ws/             # IMU package workspace (previously bno085_ws)
~/Desktop/odom/ros_ws/           # wheel_odometry workspace
~/Desktop/robot_bringup_ws/      # robot_bringup package and config
~/Desktop/slam/                  # sllidar_ros2 workspace / SLAM-related packages
```

Workspace names and locations can differ between machines. Confirm the
real paths before building or launching. The bringup launch file should
ideally locate the RPLIDAR launch file through the installed package
share directory, rather than relying on a personal absolute path.

## 4. Build the packages

For each source workspace, install dependencies with `rosdep` where
package metadata is available, then build:

``` bash
cd ~/Desktop/bno085_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Repeat for the odometry and bringup workspaces:

``` bash
cd ~/Desktop/odom/ros_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

``` bash
cd ~/Desktop/robot_bringup_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Build the RPLIDAR workspace too if `sllidar_ros2` is being built from
source:

``` bash
cd ~/Desktop/slam
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

If a workspace has no `src` directory or the package is installed from
apt, do not run the source-build commands there. Resolve missing Python
or system dependencies according to the package's own instructions. The
wheel-odometry node uses `lgpio`; the BNO085 package may require
additional I²C/sensor libraries according to its implementation.

## 5. BNO085 IMU node

### Package and topic

-   Package: `imu_node_pkg`
-   Executable: `bno085_node`
-   Node name used by bringup: `bno085_node`
-   Topic: `/imu/data`

The node has previously logged:

``` text
BNO085 IMU node started, publishing to /imu/data.
```

### Run it independently

``` bash
source /opt/ros/jazzy/setup.bash
source ~/Desktop/bno085_ws/install/setup.bash
ros2 run imu_node_pkg bno085_node
```

Check publication:

``` bash
ros2 topic list | grep imu
ros2 topic info /imu/data
ros2 topic echo /imu/data --once
ros2 topic hz /imu/data
```

Confirm the message is `sensor_msgs/msg/Imu`, the header frame is
correct, timestamps advance, units and orientation conventions are
appropriate, and the IMU is physically detected. Do not assume that
every field (especially orientation or covariance) is valid merely
because the topic exists.

### Hardware and frame notes

-   Enable the required I²C interface and verify the sensor wiring and
    power.
-   The bringup launch file defines a static transform from `base_link`
    to `imu_link` with a translation of `(0, 0, 0.05)` metres and zero
    rotation.
-   Update that transform if the IMU is mounted elsewhere or rotated
    relative to the robot frame.

## 6. Wheel odometry node

### Package and topic

-   Package: `wheel_odometry`
-   Executable: `wheel_odom`
-   Node name used by bringup: `wheel_odom`
-   Published topic: `/odom_raw` (`nav_msgs/msg/Odometry`)
-   Update timer in the saved implementation: 100 Hz

The node uses `lgpio` to read quadrature encoder inputs. The saved
implementation uses these GPIO assignments:

  Wheel                Encoder A   Encoder B
  ------------------ ----------- -----------
  Front left (FL)        GPIO 25     GPIO 24
  Front right (FR)        GPIO 5      GPIO 6
  Rear left (RL)         GPIO 26     GPIO 16
  Rear right (RR)        GPIO 17     GPIO 27

It also uses these initial parameters:

  -----------------------------------------------------------------------
  Parameter                                                         Value
  ------------------------------ ----------------------------------------
  Wheel radius                                `0.0325 m` (65 mm diameter)

  Ticks per revolution                     `8` (must be calibrated to the
                                            encoder/counting arrangement)

  Wheel base used by the                                         `0.14 m`
  differential model             

  GPIO chip number                                                    `4`
  -----------------------------------------------------------------------

**Important kinematics limitation:** The saved odometry implementation
averages the left and right wheel counts and applies
**differential-drive kinematics**. AutoBot has a mecanum chassis, so
this model does not correctly estimate lateral motion and may be
inaccurate during mecanum strafing. It should be treated as a baseline
implementation until a mecanum kinematic odometry model is implemented
and validated. Confirm GPIO chip numbering and pin numbering against the
exact Raspberry Pi OS/kernel and hardware arrangement.

### Run it independently

``` bash
source /opt/ros/jazzy/setup.bash
source ~/Desktop/odom/ros_ws/install/setup.bash
ros2 run wheel_odometry wheel_odom
```

Check output:

``` bash
ros2 topic info /odom_raw
ros2 topic echo /odom_raw --once
ros2 topic hz /odom_raw
```

### Calibration checklist

1.  Lift the wheels and rotate each wheel by hand; verify that its
    encoder count changes.
2.  Drive a measured straight-line distance and compare the reported
    distance with the tape-measured distance.
3.  Perform repeatable turns and compare the estimated heading change
    with the observed turn.
4.  Test each wheel's direction/sign.
5.  Calibrate ticks per wheel revolution and wheel radius.
6.  For mecanum motion, implement and validate the correct four-wheel
    kinematics before relying on odometry for lateral travel.

The odometry message uses `odom` as `header.frame_id` and `base_link` as
`child_frame_id`. The saved code expects the EKF to publish the odometry
TF, avoiding a second competing publisher of the same transform.

## 7. RPLIDAR C1 driver (`sllidar_ros2`)

The saved bringup launch includes:

``` text
sllidar_ros2/launch/sllidar_c1_launch.py
```

Run the driver independently (after sourcing the workspace in which it
is installed):

``` bash
source /opt/ros/jazzy/setup.bash
source ~/Desktop/slam/install/setup.bash
ros2 launch sllidar_ros2 sllidar_c1_launch.py
```

If that launch name is not installed in your version, inspect the
available launch files:

``` bash
ros2 pkg prefix sllidar_ros2
ros2 pkg executables sllidar_ros2
find "$(ros2 pkg prefix sllidar_ros2)/share/sllidar_ros2" -maxdepth 3 -type f
```

Check the scan topic:

``` bash
ros2 topic list | grep scan
ros2 topic info /scan
ros2 topic echo /scan --once
ros2 topic hz /scan
```

The usual expected topic is `/scan`, with type
`sensor_msgs/msg/LaserScan`. Confirm the message's `header.frame_id` and
make sure the matching laser frame exists in TF.

The saved bringup defines a static transform `base_link → laser` at
`(x=0.18, y=0, z=0.12)` metres, with zero rotation. Measure the real
sensor position and orientation and update the transform if needed.

If the driver cannot access the serial device, check the USB connection,
device path, permissions and whether another process is already using
the port. Use the launch parameters supported by the installed driver
version rather than assuming parameter names.

## 8. Robot bringup and EKF

### Package and launch file

-   Package: `robot_bringup`
-   Launch file: `bringup.launch.py`
-   EKF config: `config/ekf.yaml`

Launch the complete bringup using the built package:

``` bash
source /opt/ros/jazzy/setup.bash
source ~/Desktop/bno085_ws/install/setup.bash
source ~/Desktop/odom/ros_ws/install/setup.bash
source ~/Desktop/slam/install/setup.bash
source ~/Desktop/robot_bringup_ws/install/setup.bash

ros2 launch robot_bringup bringup.launch.py
```

Source only the workspaces that actually exist and are required on that
machine. If ROS cannot find a package, check `ros2 pkg prefix <package>`
and rebuild/source the appropriate workspace.

### EKF configuration

The saved `ekf.yaml` configures `robot_localization` at 50 Hz in 2D mode
and sets:

-   `odom0: /odom_raw`
-   `imu0: /imu/data`
-   `world_frame: odom`
-   `odom_frame: odom`
-   `base_link_frame: base_link`
-   `publish_tf: true`

The configuration selects planar position/velocity fields from wheel
odometry and yaw/angular velocity fields from the IMU. Check the full
boolean arrays in `config/ekf.yaml` before changing the sensor fields.
IMU message conventions and covariance values must be valid for the
selected fields to be fused correctly.

Check the fused output and TF:

``` bash
ros2 topic echo /odometry/filtered --once
ros2 topic hz /odometry/filtered
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_tools view_frames
```

There should be one authoritative publisher for each TF edge. In this
setup, the EKF is expected to publish `odom → base_link`; the wheel node
publishes the raw odometry message but not that TF.

### Static transforms in the saved launch

  Parent        Child           Translation (m)     Rotation
  ------------- --------------- ------------------- -------------
  `base_link`   `imu_link`      `(0, 0, 0.05)`      `(0, 0, 0)`
  `base_link`   `laser`         `(0.18, 0, 0.12)`   `(0, 0, 0)`
  `base_link`   `camera_link`   `(0.1, 0, 0.2)`     `(0, 0, 0)`

These are saved configuration values, not verified measurements. Adjust
them to match the physical sensor mounts. The camera transform is
associated with a legacy webcam entry in the saved launch and may need
revision for the current RealSense D421 mounting and frame IDs.

## 9. SLAM and mapping

AutoBot has used both SLAM Toolbox and RTAB-Map during development. They
are different mapping options; avoid launching two mapping nodes that
compete to publish the same map or TF without a deliberate design.

### Option A --- SLAM Toolbox (2D LiDAR SLAM)

The saved `bringup.launch.py` has its SLAM Toolbox node **commented
out**. To run it independently for a 2D LiDAR map:

``` bash
source /opt/ros/jazzy/setup.bash
ros2 launch slam_toolbox online_async_launch.py \
  use_odom:=false \
  base_frame:=base_link \
  map_frame:=map \
  scan_topic:=/scan \
  scan_qos:=sensor_data
```

This is the command previously used during AutoBot troubleshooting.
Parameter names and launch arguments can differ by installed version;
inspect the installed launch file if an argument is rejected.

Verify that `/scan` is publishing, the scan frame can be transformed
into `base_link` at scan timestamps, and the robot pose is available as
required by the chosen SLAM configuration. If SLAM reports it cannot
compute odometry or transform data is old, inspect timestamps, TF
connectivity and clock synchronization before changing mapping
parameters.

### Option B --- RTAB-Map

The saved bringup creates an `rtabmap_slam/rtabmap` node after a
4-second delay, with these important settings:

-   `frame_id: base_link`
-   `subscribe_scan: true`
-   `subscribe_rgb: true`
-   `subscribe_depth: false`
-   `approx_sync: true`
-   `Reg/Strategy: '1'`
-   `Grid/FromDepth: 'false'`
-   Remaps `scan` to `/scan`, `odom` to `/odometry/filtered`, and
    `rgb/image` to `/image_raw`
-   `--delete_db_on_start` is passed, so the database is deleted at
    startup

**Check before using this configuration:**

1.  `/image_raw` must actually exist and publish a compatible RGB image.
    The RealSense D421 is a depth/stereo device, not an RGB camera; its
    IR streams are not interchangeable with an RGB image topic.
2.  If using the D421's stereo infrared streams, configure RTAB-Map for
    stereo input and remap the left/right image and camera-info topics
    to the actual topics published by the installed RealSense driver.
    Verify the required stereo parameters and synchronization.
3.  If the goal is LiDAR-only 2D mapping, consider running SLAM Toolbox
    or a deliberately configured RTAB-Map scan-based setup without
    requiring RGB input.
4.  Remove `--delete_db_on_start` if you need to preserve the RTAB-Map
    database between runs. Keep it only when intentionally starting with
    a fresh database.
5.  Confirm the exact topic names using `ros2 topic list`; the D421
    topics previously observed include
    `/camera/camera/infra1/image_rect_raw`,
    `/camera/camera/infra2/image_rect_raw`, and their camera-info
    topics, plus `/camera/camera/depth/image_rect_raw`.

Do not describe the current RTAB-Map configuration as working visual
SLAM with the D421 until the correct image inputs, calibration, TF and
synchronization are verified.

## 10. Camera and RealSense D421 note

The saved bringup contains a legacy `v4l2_camera` node configured for
`/dev/video0`, publishing the camera frame as `camera_link`. AutoBot's
camera direction has since changed to the Intel RealSense D421.

The D421 is a depth/stereo device; RGB colour imagery is not available
as on a conventional RGB-D camera. The installed driver has previously
exposed depth and stereo infrared topics. Update the bringup launch to
start the RealSense driver and use the real frame IDs and topic names.
Do not leave the legacy webcam node enabled if it conflicts with the
actual camera setup.

## 11. Diagnostic command checklist

Run these after startup:

``` bash
ros2 node list
ros2 topic list
ros2 topic info /scan
ros2 topic echo /scan --once
ros2 topic echo /imu/data --once
ros2 topic echo /odom_raw --once
ros2 topic echo /odometry/filtered --once
ros2 run tf2_ros tf2_echo base_link laser
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_tools view_frames
```

Check publishing rates:

``` bash
ros2 topic hz /scan
ros2 topic hz /imu/data
ros2 topic hz /odom_raw
ros2 topic hz /odometry/filtered
```

Expected key topics from the established AutoBot setup include:

``` text
/scan
/imu/data
/odom_raw
/odometry/filtered
/tf
/tf_static
/map                 # only when the selected SLAM node is running and publishing
```

Use `ros2 topic info <topic>` to confirm publisher/subscriber counts and
message types. Use `ros2 topic echo <topic> --once` to confirm messages
arrive.

## 12. Common problems

  -----------------------------------------------------------------------
  Symptom                             Likely checks
  ----------------------------------- -----------------------------------
  IMU topic missing                   Check I²C wiring, enabled
                                      interface, sensor detection,
                                      dependencies, package build and
                                      node logs.

  `/odom_raw` missing                 Check encoder wiring, GPIO chip/pin
                                      mapping, `lgpio`, permissions and
                                      node logs.

  Odometry moves in the wrong         Verify encoder A/B order, wheel
  direction                           signs, wheel ordering and
                                      calibration.

  EKF output missing                  Confirm `/odom_raw` and `/imu/data`
                                      are publishing; inspect EKF logs
                                      and YAML sensor configuration.

  `TF_OLD_DATA` or transform lookup   Check system clocks, timestamps, TF
  failures                            frame names and whether transforms
                                      exist at the scan timestamp.

  SLAM map does not update            Check live `/scan`, scan-to-base
                                      transform, required odometry/pose
                                      input, QoS and SLAM node logs.

  RPLIDAR scan missing                Check USB/serial device,
                                      permissions, driver launch and
                                      configured serial port.

  RTAB-Map waits for images           Check that the configured image
                                      topic exists and matches the camera
                                      type; D421 stereo topics are not
                                      RGB.

  Launch fails due to a path          Remove hard-coded personal paths
                                      and use installed package-share
                                      paths or launch arguments.

  Multiple TF publishers conflict     Ensure each transform edge has one
                                      intended publisher; avoid running
                                      duplicate odometry/SLAM publishers
                                      unintentionally.
  -----------------------------------------------------------------------

## 13. Known configuration issues to review

Before treating the system as a reproducible release, review these
points in the source:

-   Replace hard-coded paths such as `~/Desktop/slam/install/...` and
    `/home/nagha/Desktop/robot_bringup_ws/src/...` with package-share
    lookups or configurable launch arguments.
-   Remove or replace the legacy `v4l2_camera` node if the RealSense
    D421 is the active camera.
-   Choose and document the active mapping pipeline: SLAM Toolbox for 2D
    LiDAR SLAM, or a correctly configured RTAB-Map pipeline.
-   Correct the RTAB-Map image subscriptions for the chosen camera; the
    saved `/image_raw` RGB remap is not a direct match for the D421
    stereo streams.
-   Decide whether the RTAB-Map database should be deleted at each
    launch.
-   Update wheel odometry to use mecanum kinematics if lateral movement
    is part of the odometry requirement.
-   Verify the static sensor transforms against measured physical
    positions.
-   Validate EKF covariance, sensor field selection, timestamp
    consistency and TF ownership.
-   Add a safe stop/watchdog policy in the low-level motor controller
    for communication loss; ROS odometry and SLAM are not a motor safety
    mechanism.

## 14. Recommended startup sequence

For first-time debugging, start each component separately and validate
its output before launching the full system:

1.  Start the BNO085 node and confirm `/imu/data`.
2.  Start wheel odometry and confirm `/odom_raw` while rotating wheels.
3.  Start the RPLIDAR driver and confirm `/scan`.
4.  Start the static transforms and EKF; verify `/odometry/filtered` and
    `odom → base_link`.
5.  Start **one** selected SLAM pipeline and verify map updates.
6.  Start RViz2 on the robot or a remote workstation and configure the
    correct fixed frame and topics.
7.  Only after these checks pass, use the consolidated bringup launch.

This sequence makes it easier to isolate sensor, GPIO, TF, timestamp,
configuration and SLAM errors.

## Repository

AutoBot source repository: <https://github.com/nagha2025/AutoBot>

The README documents the known package names and configuration surfaced
during development. Verify the live source files and installed package
versions before copying commands into a production setup.
