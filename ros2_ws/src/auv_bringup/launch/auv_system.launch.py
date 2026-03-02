from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        Node(
            package='auv_control',
            executable='telemetry_bridge',
            name='telemetry_bridge',
            output='screen',
        ),
        Node(
            package='auv_control',
            executable='depth_hold_controller',
            name='depth_hold_controller',
            output='screen',
        ),
        Node(
            package='auv_bringup',
            executable='mission_manager',
            name='mission_manager',
            output='screen',
        ),
    ])
