#!/usr/bin/env python3
import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String

from auv_interfaces.msg import Telemetry


class ApiBridge(Node):
    """Minimal HTTP bridge for ground station integration.

    Endpoints:
    - POST /mission {"cmd": "arm|disarm|start|stop|emergency|reset"}
    - POST /depth {"target_depth": float}
    - GET  /telemetry
    - GET  /mission/state
    - GET  /mission/event
    """

    def __init__(self) -> None:
        super().__init__('api_bridge')

        self.declare_parameter('http_host', '127.0.0.1')
        self.declare_parameter('http_port', 8080)

        self.pub_mission = self.create_publisher(String, '/auv/mission/cmd', 10)
        self.pub_depth = self.create_publisher(Float32, '/auv/cmd/target_depth', 10)

        self.create_subscription(String, '/auv/mission/state', self._on_state, 10)
        self.create_subscription(String, '/auv/mission/event', self._on_event, 10)
        self.create_subscription(Telemetry, '/auv/telemetry', self._on_telemetry, 10)

        self._mission_state = 'IDLE'
        self._mission_event = ''
        self._telemetry: Dict[str, Any] = {
            'depth_m': 0.0,
            'battery_v': 0.0,
            'battery_a': 0.0,
            'roll_deg': 0.0,
            'pitch_deg': 0.0,
            'yaw_deg': 0.0,
            'vx_mps': 0.0,
            'vy_mps': 0.0,
            'vz_mps': 0.0,
            'mode': 'UNKNOWN',
            'armed': False,
        }
        self._lock = threading.Lock()

        self._http_server = None
        self._http_thread = None
        self._start_http_server()

    def _on_state(self, msg: String) -> None:
        with self._lock:
            self._mission_state = msg.data

    def _on_event(self, msg: String) -> None:
        with self._lock:
            self._mission_event = msg.data

    def _on_telemetry(self, msg: Telemetry) -> None:
        with self._lock:
            self._telemetry = {
                'depth_m': float(msg.depth_m),
                'battery_v': float(msg.battery_v),
                'battery_a': float(msg.battery_a),
                'roll_deg': float(msg.roll_deg),
                'pitch_deg': float(msg.pitch_deg),
                'yaw_deg': float(msg.yaw_deg),
                'vx_mps': float(msg.vx_mps),
                'vy_mps': float(msg.vy_mps),
                'vz_mps': float(msg.vz_mps),
                'mode': msg.mode,
                'armed': bool(msg.armed),
            }

    def _json_response(self, handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        handler.send_response(status)
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.send_header('Content-Length', str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    def _read_json(self, handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
        length = int(handler.headers.get('Content-Length', '0'))
        raw = handler.rfile.read(length) if length > 0 else b'{}'
        return json.loads(raw.decode('utf-8'))

    def _start_http_server(self) -> None:
        node = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args):
                node.get_logger().debug(format % args)

            def do_GET(self):
                if self.path == '/telemetry':
                    with node._lock:
                        payload = dict(node._telemetry)
                    node._json_response(self, HTTPStatus.OK, payload)
                    return

                if self.path == '/mission/state':
                    with node._lock:
                        payload = {'state': node._mission_state}
                    node._json_response(self, HTTPStatus.OK, payload)
                    return

                if self.path == '/mission/event':
                    with node._lock:
                        payload = {'event': node._mission_event}
                    node._json_response(self, HTTPStatus.OK, payload)
                    return

                node._json_response(self, HTTPStatus.NOT_FOUND, {'error': 'not found'})

            def do_POST(self):
                try:
                    data = node._read_json(self)
                except Exception:
                    node._json_response(self, HTTPStatus.BAD_REQUEST, {'error': 'invalid json'})
                    return

                if self.path == '/mission':
                    cmd = str(data.get('cmd', '')).strip().lower()
                    if cmd not in {'arm', 'disarm', 'start', 'stop', 'emergency', 'reset'}:
                        node._json_response(self, HTTPStatus.BAD_REQUEST, {'error': 'invalid cmd'})
                        return
                    node.pub_mission.publish(String(data=cmd))
                    node._json_response(self, HTTPStatus.OK, {'ok': True, 'cmd': cmd})
                    return

                if self.path == '/depth':
                    try:
                        target_depth = float(data.get('target_depth'))
                    except (TypeError, ValueError):
                        node._json_response(self, HTTPStatus.BAD_REQUEST, {'error': 'invalid target_depth'})
                        return
                    node.pub_depth.publish(Float32(data=target_depth))
                    node._json_response(self, HTTPStatus.OK, {'ok': True, 'target_depth': target_depth})
                    return

                node._json_response(self, HTTPStatus.NOT_FOUND, {'error': 'not found'})

        host = str(self.get_parameter('http_host').value)
        port = int(self.get_parameter('http_port').value)
        self._http_server = ThreadingHTTPServer((host, port), Handler)
        self._http_thread = threading.Thread(target=self._http_server.serve_forever, daemon=True)
        self._http_thread.start()
        self.get_logger().info(f'api bridge serving on http://{host}:{port}')

    def destroy_node(self):
        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = ApiBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
