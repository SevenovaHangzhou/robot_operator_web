#!/usr/bin/env bash
# Build one commit of this repository as an overlay on a robot_driver install and make it the
# current release. Usage: deploy/install.sh <commit> <robot_driver install setup.bash>
# The overlay uses the running stack's interface packages, so the web speaks its messages.
# Does not touch systemd; restart the service afterwards.
set -euo pipefail

commit="${1:?commit to deploy}"
driver_setup="${2:?robot_driver install setup.bash}"
[[ "${commit}" =~ ^[0-9a-f]{40}$ ]] || { echo "commit must be a full 40-character SHA" >&2; exit 2; }

root="${HOME}/.local/share/robot-operator-web"
release="${root}/releases/${commit}"
repository="https://github.com/SevenovaHangzhou/robot_operator_web.git"

if [[ ! -d "${release}/install" ]]; then
  mkdir -p "${release}/src"
  git clone --quiet "${repository}" "${release}/src/robot_operator_web"
  git -C "${release}/src/robot_operator_web" checkout --quiet --detach "${commit}"
  (
    cd "${release}"
    set +u
    # shellcheck source=/dev/null
    source /opt/ros/humble/setup.bash
    # shellcheck source=/dev/null
    source "${driver_setup}"
    set -u
    colcon build --packages-select integ_operator_web --event-handlers console_cohesion+
  )
fi
ln -sfn "${release}" "${root}/current.new"
mv -T "${root}/current.new" "${root}/current"
echo "current -> ${release}"
