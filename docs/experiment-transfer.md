# 18141 → 18110 动作序列交接

## 使用流程

1. 在18141完成有效性及人工安全审核，等待自动准备执行批次。
2. 在18141执行区填写目标IP和端口，点击“检查并保存地址”。服务器用预置密钥验证机器人身份，浏览器不接触密钥。
3. 选择已准入批次，点击“下发所选批次”；收到回执只表示持久化完成。
4. 打开18110 `/arm#received-experiments`，登录。收到的包自动出现在“载入动作序列”列表；点击载入，仅填充固定步骤。
5. 核对装配、周围空间和起点，按原流程获取控制权并在需要时人工使能，点击“播放收到的序列”。已执行/撤回/过期包不可重复播放，重复请求只返回原执行记录。
6. 18141自动对账，下载经哈希校验的结束日志，接入本机分析。统计完整和静稳通过不表示参数验收。

改变IP前须完成旧包对账或撤回。浏览器断线保持原停止规则，没有自动续跑。默认最多50段；必须按完整测量组编排，不能静默截断。

## 一次性部署配置

本功能默认关闭。两端需要由部署者配置同一个机器人身份和至少32字节的随机共享密钥文件（权限0600）。密钥不进入Git、聊天或浏览器；HTTP传输提供签名完整性，没有内容保密，需要时使用HTTPS。

配套辨识仓库提交固定为 `15c7811f81b099f5c16e0639dbd6447810739733`，来源锁定在 `deploy/experiment-transfer.lock.json`。先检出该提交，再构建并在机器人专用目录安装：

```bash
python3 -m pip wheel --no-deps /path/to/robot_dynamic_parameter_Identification/toolchain/remote_execution --wheel-dir /path/to/wheels
python3 -m pip install --target /path/to/receiver-python /path/to/wheels/robot_experiment_transfer-1.1.0-py3-none-any.whl
```

由服务环境显式设置：

```text
OPERATOR_WEB_PYTHONPATH=/path/to/receiver-python
ROBOT_EXPERIMENT_RECEIVER_CONFIG=/path/to/receiver.json
```

`receiver.json`字段模板位于辨识仓库 `toolchain/remote_execution/receiver.example.json`。初次使用inspection模式验证安装，execution模式才接收动作。`runtime_context`必须由真实现场事实提供装配、控制模型SHA、PID/前馈状态、录制目录/实例、ROS与MCAP时钟关系、采样缺口限制和有效期限；不得填造这些值让检查通过。18141使用同目录的 `workstation.example.json` 配置身份、密钥和初始origin，后续可在UI中换IP。

安装和重载本网页需单独部署窗口；以上代码开发与单元测试不代表现场安装或运动验收。原运行栈、模型及planner版本应先对齐；本改动同步此前已验证的ca60e495停止连续性修复，与18141审核规划器一致；不改compat/deps pin。

## 接口

- `POST /api/arm/experiment-transfer`：HMAC认证的数据传输，拒绝start/enable/reset/stop操作。
- `GET /api/arm/experiment-packages`、`GET /api/arm/experiment-packages/{package_id}`：原网页登录cookie，列表和只读载入预览。
- `/ws/arm`：`run_experiment_package`只接受`package_id`和`request_id`，由机器人读取本地不可变包；原控制权、模式、反馈、使能、限位及起点检查继续生效。
- 兼容的独立 `/arm/experiments` 页面仍保留，日常入口使用原机械臂页面。

## 开发验证

仓库测试：`test_arm_experiments.py`、原console/page/ROS send/authority测试及 `node integ_operator_web/test/test_received_sequences.mjs`。跨仓库集成测试在辨识仓库执行，将 `FIELD_OPERATOR_ROOT` 显式指向本源码仓库，并单独运行 `toolchain/tests/test_remote_field_adapter.py`；仅假驱动、不连接ROS设备。接收协议和完整回传的测试在该仓库 `test_remote_execution.py`。
