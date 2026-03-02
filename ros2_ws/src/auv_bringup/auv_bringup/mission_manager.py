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


_ALLOWED_TRANSITIONS = {
    MissionState.IDLE: {
        'arm': MissionState.ARMED,
        'emergency': MissionState.EMERGENCY,
    },
    MissionState.ARMED: {
        'disarm': MissionState.IDLE,
        'start': MissionState.MISSION,
        'emergency': MissionState.EMERGENCY,
    },
    MissionState.MISSION: {
        'stop': MissionState.ARMED,
        'emergency': MissionState.EMERGENCY,
    },
    MissionState.EMERGENCY: {
        'reset': MissionState.IDLE,
    },
}


class MissionManager(Node):
    def __init__(self) -> None:
        super().__init__('mission_manager')
        self.state = MissionState.IDLE

        self.create_subscription(String, '/auv/mission/cmd', self.on_command, 10)
        self.pub_state = self.create_publisher(String, '/auv/mission/state', 10)
        self.pub_event = self.create_publisher(String, '/auv/mission/event', 10)
        self.timer = self.create_timer(0.5, self.publish_state)

    def on_command(self, msg: String) -> None:
        cmd = msg.data.strip().lower()
        next_state = _ALLOWED_TRANSITIONS.get(self.state, {}).get(cmd)
        if next_state is None:
            self._publish_event(f'reject:{cmd}:from:{self.state.value}')
            self.get_logger().warning(f'rejected mission command={cmd}, state={self.state.value}')
            return

        prev_state = self.state
        self.state = next_state
        self._publish_event(f'accept:{cmd}:{prev_state.value}->{self.state.value}')
        self.get_logger().info(f'mission command={cmd}, {prev_state.value}->{self.state.value}')

    def _publish_event(self, text: str) -> None:
        msg = String()
        msg.data = text
        self.pub_event.publish(msg)

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
