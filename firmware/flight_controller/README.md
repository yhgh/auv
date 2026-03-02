# 飞控层说明（ArduSub/PX4 参考实现）

本目录用于管理底层飞控配置与硬件映射。

## 已集成的开源飞控来源

仓库内提供了 `fetch_open_source_fc.sh`，用于将 ArduPilot（包含 ArduSub）直接克隆到：

- `firmware/flight_controller/ardupilot`

执行方式：

```bash
cd firmware/flight_controller
bash fetch_open_source_fc.sh
```

也可指定你上传的网盘直链或本地压缩包：

```bash
# 指定网盘/直链
bash fetch_open_source_fc.sh --archive-url "<YOUR_URL>"

# 指定本地压缩包
bash fetch_open_source_fc.sh --archive /path/to/ardupilot.tar.gz
```

> 说明：脚本默认先尝试下载 Google Drive 共享包（当前预置了你提供的链接），失败后自动回退到 GitHub/Gitee clone。

## 建议硬件

- 飞控：Pixhawk 4/6 系列
- IMU/磁罗盘：飞控内置 + 外置罗盘（可选）
- 深度计：MS5837 或同类
- 推进器：6~8 推进器布局（X/矢量）

## 通信建议

- 主控机（NVIDIA Jetson / x86）与飞控：
  - 串口：`/dev/ttyACM0`（921600）
  - 或 UDP：`udp://0.0.0.0:14550`
- 协议：MAVLink v2

## 参数模板

示例参数见 `params/ardusub_example.params`。

> 注意：实际下水前请做推进器方向、重心浮心、深度计零偏与失联策略联调。
