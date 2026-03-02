#!/usr/bin/env python3
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

from auv_interfaces.msg import Telemetry


class DepthHoldController(Node):
    def __init__(self) -> None:
        super().__init__('depth_hold_controller')
        self.target_depth = 2.0
        self.current_depth = 0.0

        self.declare_parameter('kp', 45.0)
        self.declare_parameter('ki', 6.0)
        self.declare_parameter('kd', 18.0)
        self.declare_parameter('max_cmd', 100.0)
        self.declare_parameter('integral_limit', 15.0)
        self.declare_parameter('depth_deadband_m', 0.03)

        self._i_term = 0.0
        self._last_error = 0.0
        self._last_t = time.monotonic()
        self._armed = False

        self.create_subscription(Float32, '/auv/cmd/target_depth', self.on_target_depth, 10)
        self.create_subscription(Telemetry, '/auv/telemetry', self.on_telemetry, 10)
        self.pub_thrust_z = self.create_publisher(Float32, '/auv/cmd/thrust_z', 10)
        self.timer = self.create_timer(0.05, self.control_loop)

    def on_target_depth(self, msg: Float32) -> None:
        self.target_depth = max(msg.data, 0.0)

    def on_telemetry(self, msg: Telemetry) -> None:
        self.current_depth = msg.depth_m
        self._armed = bool(msg.armed)

    def control_loop(self) -> None:
        now = time.monotonic()
        dt = max(now - self._last_t, 1e-3)
        self._last_t = now

        if not self._armed:
            self._i_term = 0.0
            self._last_error = 0.0
            self.pub_thrust_z.publish(Float32(data=0.0))
            return

        error = self.target_depth - self.current_depth
        if abs(error) < float(self.get_parameter('depth_deadband_m').value):
            error = 0.0

        kp = float(self.get_parameter('kp').value)
        ki = float(self.get_parameter('ki').value)
        kd = float(self.get_parameter('kd').value)
        max_cmd = float(self.get_parameter('max_cmd').value)
        integral_limit = float(self.get_parameter('integral_limit').value)

        self._i_term += error * dt
        self._i_term = max(min(self._i_term, integral_limit), -integral_limit)
        d_term = (error - self._last_error) / dt
        self._last_error = error

        cmd = kp * error + ki * self._i_term + kd * d_term
        cmd = max(min(cmd, max_cmd), -max_cmd)

        self.pub_thrust_z.publish(Float32(data=float(cmd)))


def main() -> None:
    rclpy.init()
    node = DepthHoldController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
