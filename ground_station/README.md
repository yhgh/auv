# 地面站（CLI 原型）

该原型用于演示地面站核心能力：

1. 读取遥测（JSON 行）
2. 发送任务命令（arm/start/stop/emergency）
3. 设置目标深度

## 用法

```bash
python3 gcs_cli.py telemetry --source telemetry.jsonl
python3 gcs_cli.py mission --cmd arm
python3 gcs_cli.py depth --meters 3.5
```

> 当前命令发送通过 HTTP stub 演示，可替换为 rosbridge/websocket 或自定义 API 网关。
