# AUV 基本功能全栈项目（飞控 + ROS2 主控 + 地面站）

本项目参考了开源 AUV/ROV 常见方案（ArduSub/PX4 + MAVLink + ROS2 + 地面站）的分层思路，提供一个可扩展的最小可用实现：

- **底层飞控层**：基于 ArduSub/PX4 思路进行参数与接口约束。
- **主控 ROS2 层**：负责任务状态机、速度闭环、指令分发、遥测汇聚。
- **地面站层**：显示遥测、发送任务控制与手动控制指令。

> 当前版本以“可读、可改、可跑通开发流程”为目标，适合做二次开发起点。

## 目录结构

```text
.
├── firmware/
│   └── flight_controller/
│       ├── README.md
│       └── params/
│           └── ardusub_example.params
├── ros2_ws/
│   └── src/
│       ├── auv_interfaces/
│       │   └── msg/
│       │       └── Telemetry.msg
│       ├── auv_bringup/
│       │   ├── launch/
│       │   │   └── auv_system.launch.py
│       │   ├── package.xml
│       │   ├── setup.py
│       │   └── auv_bringup/
│       │       ├── __init__.py
│       │       └── mission_manager.py
│       └── auv_control/
│           ├── package.xml
│           ├── setup.py
│           └── auv_control/
│               ├── __init__.py
│               ├── depth_hold_controller.py
│               └── telemetry_bridge.py
├── ground_station/
│   ├── README.md
│   └── gcs_cli.py
└── scripts/
    └── dev_run.sh
```

## 系统设计

### 1) 飞控层（firmware/flight_controller）

- 推荐协议：MAVLink
- 典型连接：主控机（ROS2）通过串口/UDP 连接飞控
- 参数示例：提供了推进器布局、深度控制、失联保护的参数模板

### 2) ROS2 主控层（ros2_ws/src）

包含三个逻辑组件：

- **telemetry_bridge**：采集飞控数据并发布 `/auv/telemetry`
- **depth_hold_controller**：订阅期望深度和当前深度，发布 `/auv/cmd/thrust_z`
- **mission_manager**：任务状态机（IDLE/ARMED/MISSION/EMERGENCY），对外提供 `arm/disarm/start/stop/emergency` 接口

### 3) 地面站层（ground_station）

- 轻量命令行版本（可直接跑）
- 可查看遥测（JSON 行）
- 可发送控制指令到 ROS2 主控（当前以 HTTP stub 形式演示，可替换成 rosbridge/WebSocket）

## 快速开始

### A. ROS2 侧（逻辑开发）

> 需要本机具备 ROS2 Humble/Iron 及 rclpy 环境。

```bash
cd ros2_ws
colcon build
source install/setup.bash
ros2 launch auv_bringup auv_system.launch.py
```

### B. 地面站侧

```bash
cd ground_station
python3 gcs_cli.py --help
```

### C. 一键开发脚本

```bash
bash scripts/dev_run.sh
```

## 后续可扩展方向

1. 将 `telemetry_bridge.py` 改为真实 MAVLink 接入（pymavlink/mavros2）。
2. 用 EKF 融合 DVL/IMU/深度计，形成统一 `/odom`。
3. 在 `mission_manager.py` 中加入航点、返航、失联上浮策略。
4. 地面站改为 Web UI（FastAPI + Vue/React）并对接视频流。

## 开源参考建议

- ArduSub / ArduPilot
- PX4 + ROS2
- MAVLink / mavros / mavros2
- QGroundControl

