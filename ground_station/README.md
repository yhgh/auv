# 地面站（CLI 原型）

该原型用于演示地面站核心能力：

1. 读取实时遥测（通过 `api_bridge`）
2. 发送任务命令（arm/start/stop/emergency）
3. 设置目标深度

## 用法

```bash
python3 gcs_cli.py telemetry
python3 gcs_cli.py mission --cmd arm
python3 gcs_cli.py depth --meters 3.5
```

## 可选参数

```bash
python3 gcs_cli.py --api-base http://127.0.0.1:8080 telemetry
```

> 兼容历史模式：`telemetry --source telemetry.jsonl` 仍可读取本地 JSON 行文件。
