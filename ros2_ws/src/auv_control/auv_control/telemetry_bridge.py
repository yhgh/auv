#!/usr/bin/env python3
import math
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

from auv_interfaces.msg import Telemetry

try:
    from pymavlink import mavutil
except ImportError:  # optional dependency in local dev
    mavutil = None


class TelemetryBridge(Node):
    """Telemetry + actuator bridge for AUV flight controller.

    - If pymavlink is available and `mavlink_url` is configured, reads real MAVLink telemetry.
    - If unavailable, falls back to deterministic simulated telemetry for local development.
    - For real FC links, also forwards `/auv/cmd/thrust_z` to MAVLink RC override.
    """

    def __init__(self) -> None:
        super().__init__('telemetry_bridge')

        self.declare_parameter('mavlink_url', 'udp:127.0.0.1:14550')
        self.declare_parameter('sim_mode', False)
        self.declare_parameter('mavlink_heartbeat_timeout_s', 8.0)
        self.declare_parameter('throttle_rc_channel', 3)
        self.declare_parameter('throttle_pwm_min', 1100)
        self.declare_parameter('throttle_pwm_trim', 1500)
        self.declare_parameter('throttle_pwm_max', 1900)

        self.publisher = self.create_publisher(Telemetry, '/auv/telemetry', 10)
        self.create_subscription(Float32, '/auv/cmd/thrust_z', self.on_thrust_cmd, 10)

        self.start_time = time.time()
        self._last_heartbeat = 0.0

        self._depth_m = 0.0
        self._battery_v = 0.0
        self._battery_a = 0.0
        self._roll_deg = 0.0
        self._pitch_deg = 0.0
        self._yaw_deg = 0.0
        self._vx_mps = 0.0
        self._vy_mps = 0.0
        self._vz_mps = 0.0
        self._armed = False
        self._mode = 'UNKNOWN'

        self.master = self._connect_mavlink()

        self.timer = self.create_timer(0.1, self.on_timer)

    def _connect_mavlink(self):
        sim_mode = bool(self.get_parameter('sim_mode').value)
        if sim_mode:
            self.get_logger().info('telemetry_bridge running in sim_mode=true')
            return None

        if mavutil is None:
            self.get_logger().warning('pymavlink not installed, fallback to simulated telemetry')
            return None

        mavlink_url = str(self.get_parameter('mavlink_url').value)
        try:
            master = mavutil.mavlink_connection(mavlink_url)
            master.wait_heartbeat(timeout=float(self.get_parameter('mavlink_heartbeat_timeout_s').value))
            self._last_heartbeat = time.time()
            self.get_logger().info(f'connected to mavlink endpoint: {mavlink_url}')
            return master
        except Exception as exc:
            self.get_logger().warning(f'failed to connect mavlink ({exc}), fallback to simulated telemetry')
            return None

    def on_thrust_cmd(self, msg: Float32) -> None:
        if self.master is None:
            return

        pwm_min = int(self.get_parameter('throttle_pwm_min').value)
        pwm_trim = int(self.get_parameter('throttle_pwm_trim').value)
        pwm_max = int(self.get_parameter('throttle_pwm_max').value)
        channel = int(self.get_parameter('throttle_rc_channel').value)

        thrust = max(min(float(msg.data), 100.0), -100.0)
        if thrust >= 0:
            pwm = int(pwm_trim + (pwm_max - pwm_trim) * (thrust / 100.0))
        else:
            pwm = int(pwm_trim + (pwm_trim - pwm_min) * (thrust / 100.0))

        # 8 channels RC override; 65535 means ignore channel
        rc = [65535] * 8
        if 1 <= channel <= 8:
            rc[channel - 1] = pwm

        self.master.mav.rc_channels_override_send(
            self.master.target_system,
            self.master.target_component,
            *rc,
        )

    def _poll_mavlink(self) -> None:
        if self.master is None:
            return

        for _ in range(50):
            m = self.master.recv_match(blocking=False)
            if m is None:
                break

            mtype = m.get_type()
            if mtype == 'HEARTBEAT':
                self._last_heartbeat = time.time()
                self._armed = bool(m.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                try:
                    self._mode = mavutil.mode_string_v10(m)
                except Exception:
                    self._mode = 'UNKNOWN'
            elif mtype == 'ATTITUDE':
                self._roll_deg = math.degrees(m.roll)
                self._pitch_deg = math.degrees(m.pitch)
                self._yaw_deg = math.degrees(m.yaw) % 360.0
            elif mtype == 'SYS_STATUS':
                self._battery_v = float(m.volt_battery) / 1000.0 if m.volt_battery > 0 else self._battery_v
                self._battery_a = float(m.current_battery) / 100.0 if m.current_battery > -1 else self._battery_a
            elif mtype == 'LOCAL_POSITION_NED':
                self._vx_mps = float(m.vx)
                self._vy_mps = float(m.vy)
                self._vz_mps = float(m.vz)
            elif mtype in ('SCALED_PRESSURE', 'SCALED_PRESSURE2', 'SCALED_PRESSURE3'):
                # Rough conversion in seawater: 1 bar ~= 10m depth. Gauge from 1.01325 bar atmosphere.
                self._depth_m = max(0.0, (float(m.press_abs) - 1013.25) / 100.0 * 10.0)

        timeout_s = float(self.get_parameter('mavlink_heartbeat_timeout_s').value)
        if self._last_heartbeat and (time.time() - self._last_heartbeat > timeout_s):
            self.get_logger().warning('mavlink heartbeat timeout, switching to simulated telemetry')
            self.master = None

    def _publish_simulated(self) -> None:
        elapsed = time.time() - self.start_time
        self._depth_m = 2.0 + 0.4 * math.sin(elapsed * 0.3)
        self._battery_v = 15.8 - 0.001 * elapsed
        self._battery_a = 4.0 + 0.5 * math.sin(elapsed)
        self._roll_deg = 1.0 * math.sin(elapsed * 0.2)
        self._pitch_deg = 1.2 * math.sin(elapsed * 0.25)
        self._yaw_deg = (elapsed * 3.0) % 360.0
        self._vx_mps = 0.2
        self._vy_mps = 0.0
        self._vz_mps = 0.0
        self._mode = 'SIM_DEPTH_HOLD'
        self._armed = True

    def on_timer(self) -> None:
        if self.master is not None:
            self._poll_mavlink()
        else:
            self._publish_simulated()

        msg = Telemetry()
        msg.stamp = self.get_clock().now().to_msg()
        msg.depth_m = float(self._depth_m)
        msg.battery_v = float(self._battery_v)
        msg.battery_a = float(self._battery_a)
        msg.roll_deg = float(self._roll_deg)
        msg.pitch_deg = float(self._pitch_deg)
        msg.yaw_deg = float(self._yaw_deg)
        msg.vx_mps = float(self._vx_mps)
        msg.vy_mps = float(self._vy_mps)
        msg.vz_mps = float(self._vz_mps)
        msg.mode = self._mode
        msg.armed = self._armed
        self.publisher.publish(msg)


def main() -> None:
    rclpy.init()
    node = TelemetryBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
