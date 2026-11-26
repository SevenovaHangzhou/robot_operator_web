# robot_operator_web

RT-Control 操作网页：一个进程、一个端口，页面有状态（首页）、底盘、机械臂与头部。只给台架与调试使用。
2026-11-16 从 [robot_driver](https://github.com/SevenovaHangzhou/robot_driver) 拆出（ELECTRI-209），
保留 `src/rt_control/integ_operator_web` 自 #159 起的提交历史。页面功能与边界见
[integ_operator_web/README.md](integ_operator_web/README.md)。

网页仍属 RT-Control 域：它和运行栈一起部署，可以使用下面列出的 RT-Control 内部接口。
它不启动硬件、不写驱动控制字、不自动使能或复位。

## 目录

| 路径 | 内容 |
| --- | --- |
| `integ_operator_web/` | ROS 2 Humble 包（aiohttp 服务、网页静态资源、测试） |
| `deps.repos` | 构建依赖：`robot_interfaces` 的固定提交 |
| `compat.yaml` | 适配的 `robot_driver` 固定提交 |
| `tools/check_compat.py` | 检查两边固定的 `robot_interfaces` 一致，并给出模型提交 |
| `tools/pr_contract_gate.py` | PR 描述合同检查（与 robot_driver 相同） |

## 版本

- `compat.yaml` 固定一个 `robot_driver` 提交，它同时决定：
  - `robot_interfaces`：本仓库 `deps.repos` 必须固定同一个提交（CI 检查）；
  - 模型：`robot_driver` 的 `src/description/source-lock.yaml` 里的 `robot_description` 提交。
    目标机上网页叠加在 `robot_driver` 的安装之上，用的就是那份已安装的 `robot_description`。
  - 下面列出的内部接口的行为。
- 升级 `robot_driver` 时：改 `compat.yaml`；若它的 `robot_interfaces` 变了，同步改 `deps.repos`；
  跑 `python3 tools/check_compat.py` 与测试，开 PR。

## 使用的接口

公共接口（`robot_interfaces` 的 `contract/endpoints.yaml`）：
`/rt/enable`、`/rt/disable`、`/rt/reset_fault`、`/rt/capabilities`、`/rt/readiness`、`/diagnostics`、
`/joint_states`、`/rt/base/odom`、`/rt/battery/{left,right}/state`、`/rt/ultrasonic/channel1..8/range`、
`/rt/arms/set_control_mode`、`/rt/arms/rolling/state`、`/rt/arms/follow_joint_trajectory`、
`/rt/vacuum/{left,right}/pressure`、`/rt/head/move`。

台架替代发送方（N-04、M-09 的约束里登记，与 Motion 互斥）：`/rt/base/cmd_vel`、
`/rt/arms/rolling/target_batch`（经 `robot_interfaces_rolling_client`）。

RT-Control 内部接口（不进公共仓库；行为以 `compat.yaml` 固定的 `robot_driver` 为准）：

| 接口 | 用途 |
| --- | --- |
| `/controller_manager/list_controllers`、`/controller_manager/list_hardware_components` | 控制器与硬件组件状态 |
| `/controller_manager/get_parameters`、各控制器 `get_parameters` | 运行中的模型（`robot_description`）、关节列表、限位 |
| `/enable_manager/get_parameters`（`motion_groups`、`<组>.motion_joints`）、`/<enable_manager>/<组>/confirm_standstill` | 机械臂所在运动组的关节、停稳确认 |
| `/<controller>/controller_state`、`/<controller>/query_state`、FJT `/_action/status` | 手臂轨迹执行状态 |
| 诊断条目 `/robot/rt_control/enable_manager` | 使能状态与阶段 |

## 构建与测试

```bash
mkdir -p ~/ws/src && cd ~/ws/src
git clone https://github.com/SevenovaHangzhou/robot_operator_web.git
vcs import < robot_operator_web/deps.repos
cd ~/ws && source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-up-to integ_operator_web
colcon test --packages-select integ_operator_web && colcon test-result --verbose
```

仓库工具：`python3 -m unittest discover -s tools/tests -t .`、`python3 tools/check_compat.py`、`ruff check .`。

## 部署（systemd 用户服务）

网页在叠加于目标机 `robot_driver` 安装之上的工作区里构建，带上 `deps.repos` 固定的 `robot_interfaces`；
`robot_driver` 提供模型与其余依赖。部署前确认运行栈的接口定义与固定提交一致（`compat.yaml` 的版本自动满足；
更旧的运行栈要逐文件比对它安装的 `.msg/.srv/.action`）。

```bash
# 1. 构建指定提交并切为 current（~/.local/share/robot-operator-web/releases/<commit>）
deploy/install.sh <commit> <robot_driver 安装的 setup.bash>
# 2. 本机配置：复制模板后逐项填写，没有默认值
mkdir -p ~/.config/robot-operator-web
cp deploy/robot-operator-web.env.example ~/.config/robot-operator-web/env
# 3. 安装并启动服务
cp deploy/robot-operator-web.service ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now robot-operator-web
```

升级：对新提交运行 `deploy/install.sh`，再 `systemctl --user restart robot-operator-web`；回滚同理指向旧提交。
`deploy/start.sh` 只读取环境文件中的值；`OPERATOR_WEB_VIEW_MODEL` 填该机型的模型文件（与 `robot_driver`
机型 manifest 的 `xacro_file` 一致）。页面功能与启动参数见 [integ_operator_web/README.md](integ_operator_web/README.md)。

## 可选：18141动作包接收

工作站发送完整签名数据包，机器人本地持久化后，操作员在 `/arm` 的“载入动作序列 · 来自18141”中选择并载入，再点击“播放收到的序列”。接收列表每5秒更新；载入不使能、不获取控制权、不运动。载入后目标、档位及停留锁定；普通位姿库和预设继续保留。停止、断线和控制权规则仍由原ArmConsole处理，当前不是断网自主执行。

可选Python包 `robot-experiment-transfer==1.1.0` 由 [robot_dynamic_parameter_Identification](https://github.com/SevenovaHangzhou/robot_dynamic_parameter_Identification) 的 `toolchain/remote_execution` 构建。机器人不需要18141、MuJoCo或分析库。使用固定提交构建并核验wheel后安装到专用目录；设置 `OPERATOR_WEB_PYTHONPATH` 指向该目录，`ROBOT_EXPERIMENT_RECEIVER_CONFIG` 指向机器人本地接收配置。未设置接收配置时不导入依赖、不注册接收路由，原操作保持不变；开启时缺依赖直接报错，不静默降级。

部署配置和验证步骤见 [动作包交接](docs/experiment-transfer.md)。该扩展仅增加HTTP数据传输和既有WebSocket命令，不增加ROS/硬件接口。接收端只接受绑定当前模型、规划器、关节顺序、逐轴单位、档位和现场上下文的签名包；配置不同必须重新生成并审核，不能通过复制哈希解锁。
