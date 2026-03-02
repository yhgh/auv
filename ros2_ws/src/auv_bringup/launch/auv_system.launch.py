import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    default_params = os.path.join(
        get_package_share_directory('auv_bringup'),
        'config',
        'auv_system.params.yaml',
    )
    params_file = LaunchConfiguration('params_file')

    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=default_params,
            description='Path to ROS2 parameter YAML for AUV system nodes',
        ),
        Node(
            package='auv_control',
            executable='telemetry_bridge',
            name='telemetry_bridge',
            output='screen',
            parameters=[params_file],
        ),
        Node(
            package='auv_control',
            executable='depth_hold_controller',
            name='depth_hold_controller',
            output='screen',
            parameters=[params_file],
        ),
        Node(
            package='auv_bringup',
            executable='mission_manager',
            name='mission_manager',
            output='screen',
            parameters=[params_file],
        ),
        Node(
            package='auv_bringup',
            executable='api_bridge',
            name='api_bridge',
            output='screen',
            parameters=[params_file],
        ),
    ])
