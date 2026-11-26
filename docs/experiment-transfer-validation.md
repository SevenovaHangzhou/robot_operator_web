# 动作序列交接验证（2026-11-26）

源码基于1cb9e5d；接收依赖固定在deploy/experiment-transfer.lock.json。用户授权开发、验证、提交和推送；本轮没有部署或操作实机。

- 原console/page/ROS send/authority/modes/CSP、签名包入口及停止插值：211项通过。`source /opt/ros/humble/setup.bash`，使用本机已构建的ROS接口、临时aiohttp依赖；假驱动、回环服务、ROS_LOCALHOST_ONLY=1、隔离Domain 219。
- 与18141源码联合：10项真实ArmConsole＋假驱动测试通过，包含15轴固定升降、停止、模式切换后起点复核和ROS事件失败；未创建实机控制节点。
- `node integ_operator_web/test/test_received_sequences.mjs`：目录刷新、只读载入、过期/撤回/已执行拒绝、重试ID及离线失败通过；无运动请求。
- `ruff check --no-cache .`、`shellcheck deploy/*.sh`、9项仓库工具单元测试和`git diff --check`通过。
- `tools/check_compat.py`的网络请求被重置；随后对本机Git中的精确固定提交84a986abdf1857db9a8713e1ee221fd68015e91f调用同一个check函数，接口匹配、findings为空。模型提交09a7ca433ff48083dbac4edfa0eb3c10a3bfb781。
- 初次测试缺Python导入路径未能收集；补齐现有依赖后通过，未将未运行的测试标通过。

同步ca60e495停止连续性规划器，ArmConsole实际使用完整相位插值；接管超期在发送前拒绝，不能报告停止已确认。普通播放不使用实验事件接口，未配置接收端不导入共享包。

未验证：C++/RollingSender完整重构建、现场运行版本/模型/PID/载荷/时钟/录制、生产密钥安装、实机播放与断网自主运行。载入不执行；播放继续由用户在18110手动启动，原断线停止规则保留。
