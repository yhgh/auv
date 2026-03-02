#!/usr/bin/env python3
import math
import time

import rclpy
from rclpy.node import Node

from auv_interfaces.msg import Telemetry


class TelemetryBridge(Node):
    """Development telemetry bridge.

    In production, replace simulated data with MAVLink subscription.
    """

    def __init__(self) -> None:
        super().__init__('telemetry_bridge')
        self.publisher = self.create_publisher(Telemetry, '/auv/telemetry', 10)
        self.start_time = time.time()
        self.timer = self.create_timer(0.2, self.on_timer)

    def on_timer(self) -> None:
        elapsed = time.time() - self.start_time
        msg = Telemetry()
        msg.stamp = self.get_clock().now().to_msg()
        msg.depth_m = 2.0 + 0.4 * math.sin(elapsed * 0.3)
        msg.battery_v = 15.8 - 0.001 * elapsed
        msg.battery_a = 4.0 + 0.5 * math.sin(elapsed)
        msg.roll_deg = 1.0 * math.sin(elapsed * 0.2)
        msg.pitch_deg = 1.2 * math.sin(elapsed * 0.25)
        msg.yaw_deg = (elapsed * 3.0) % 360.0
        msg.vx_mps = 0.2
        msg.vy_mps = 0.0
        msg.vz_mps = 0.0
        msg.mode = 'DEPTH_HOLD'
        msg.armed = True
        self.publisher.publish(msg)


def main() -> None:
    rclpy.init()
    node = TelemetryBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
