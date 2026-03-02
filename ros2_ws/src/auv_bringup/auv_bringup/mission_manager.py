#!/usr/bin/env python3
from enum import Enum

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MissionState(Enum):
    IDLE = 'IDLE'
    ARMED = 'ARMED'
    MISSION = 'MISSION'
    EMERGENCY = 'EMERGENCY'


class MissionManager(Node):
    def __init__(self) -> None:
        super().__init__('mission_manager')
        self.state = MissionState.IDLE

        self.create_subscription(String, '/auv/mission/cmd', self.on_command, 10)
        self.pub_state = self.create_publisher(String, '/auv/mission/state', 10)
        self.timer = self.create_timer(0.5, self.publish_state)

    def on_command(self, msg: String) -> None:
        cmd = msg.data.strip().lower()
        transitions = {
            'arm': MissionState.ARMED,
            'disarm': MissionState.IDLE,
            'start': MissionState.MISSION,
            'stop': MissionState.ARMED,
            'emergency': MissionState.EMERGENCY,
            'reset': MissionState.IDLE,
        }
        if cmd in transitions:
            self.state = transitions[cmd]
            self.get_logger().info(f'mission command={cmd}, state={self.state.value}')
        else:
            self.get_logger().warning(f'unknown mission command={cmd}')

    def publish_state(self) -> None:
        msg = String()
        msg.data = self.state.value
        self.pub_state.publish(msg)


def main() -> None:
    rclpy.init()
    node = MissionManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
