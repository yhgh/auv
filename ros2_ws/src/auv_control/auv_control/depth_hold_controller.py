#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

from auv_interfaces.msg import Telemetry


class DepthHoldController(Node):
    def __init__(self) -> None:
        super().__init__('depth_hold_controller')
        self.target_depth = 2.0
        self.current_depth = 0.0
        self.kp = 30.0

        self.create_subscription(Float32, '/auv/cmd/target_depth', self.on_target_depth, 10)
        self.create_subscription(Telemetry, '/auv/telemetry', self.on_telemetry, 10)
        self.pub_thrust_z = self.create_publisher(Float32, '/auv/cmd/thrust_z', 10)
        self.timer = self.create_timer(0.1, self.control_loop)

    def on_target_depth(self, msg: Float32) -> None:
        self.target_depth = msg.data

    def on_telemetry(self, msg: Telemetry) -> None:
        self.current_depth = msg.depth_m

    def control_loop(self) -> None:
        error = self.target_depth - self.current_depth
        thrust_cmd = Float32()
        thrust_cmd.data = max(min(self.kp * error, 100.0), -100.0)
        self.pub_thrust_z.publish(thrust_cmd)


def main() -> None:
    rclpy.init()
    node = DepthHoldController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
