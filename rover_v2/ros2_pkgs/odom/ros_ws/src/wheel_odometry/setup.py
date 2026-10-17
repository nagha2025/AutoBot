from setuptools import setup

package_name = 'wheel_odometry'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nagha',
    maintainer_email='nagha@local',
    description='Wheel odometry node',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'wheel_odom = wheel_odometry.odom_node:main',
        ],
    },
)
