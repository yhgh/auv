#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/3] Python syntax check"
python3 -m py_compile \
  "$ROOT_DIR"/ground_station/gcs_cli.py \
  "$ROOT_DIR"/ros2_ws/src/auv_control/auv_control/telemetry_bridge.py \
  "$ROOT_DIR"/ros2_ws/src/auv_control/auv_control/depth_hold_controller.py \
  "$ROOT_DIR"/ros2_ws/src/auv_bringup/auv_bringup/mission_manager.py

echo "[2/3] Launch file lint (optional: requires ROS2 launch python package)"
if python3 -c "import launch" >/dev/null 2>&1; then
  python3 -c "import importlib.util; spec = importlib.util.spec_from_file_location('auv_launch', '$ROOT_DIR/ros2_ws/src/auv_bringup/launch/auv_system.launch.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)"
else
  echo "[warn] ROS2 launch package not found, skip launch import check"
fi

echo "[3/3] Done. For ROS2 runtime: cd $ROOT_DIR/ros2_ws && colcon build && source install/setup.bash && ros2 launch auv_bringup auv_system.launch.py"
