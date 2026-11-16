#!/usr/bin/env bash
# Start the operator web of one deployment. Never starts hardware or enables axes.
# Every machine-specific value comes from the environment file given by the systemd unit
# (deploy/robot-operator-web.env.example); nothing here is guessed.
set -euo pipefail

: "${ROBOT_DRIVER_SETUP:?robot_driver install setup.bash the web overlays}"
: "${OPERATOR_WEB_INSTALL:?install directory of this web build}"
: "${OPERATOR_WEB_BIND_HOST:?explicit interface IP}"
: "${OPERATOR_WEB_PORT:?port}"
: "${OPERATOR_WEB_CPUS:?non-realtime CPUs, e.g. 0,2,4}"
: "${ROS_DOMAIN_ID:?isolated ROS domain of the running stack}"
: "${RT_OPERATOR_WEB_TOKEN_FILE:?token file (mode 0600)}"

set +u
source /opt/ros/humble/setup.bash
source "${ROBOT_DRIVER_SETUP}"
source "${OPERATOR_WEB_INSTALL}/setup.bash"
set -u
if [[ -n "${OPERATOR_WEB_PYTHONPATH:-}" ]]; then
  export PYTHONPATH="${OPERATOR_WEB_PYTHONPATH}:${PYTHONPATH:-}"
fi

args=(
  --bind-host "${OPERATOR_WEB_BIND_HOST}"
  --port "${OPERATOR_WEB_PORT}"
  --cpus "${OPERATOR_WEB_CPUS}"
)
if [[ -n "${OPERATOR_WEB_VIEW_MODEL:-}" ]]; then
  args+=(--view-model "${OPERATOR_WEB_VIEW_MODEL}")
fi
# Extra launcher options of this deployment, e.g. --config or --software-test-only.
read -r -a extra <<<"${OPERATOR_WEB_EXTRA_ARGS:-}"
exec taskset -c "${OPERATOR_WEB_CPUS}" \
  "${OPERATOR_WEB_INSTALL}/lib/integ_operator_web/integ_operator_web" "${args[@]}" "${extra[@]}"
