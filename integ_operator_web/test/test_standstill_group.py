"""enable_manager motion groups: the arm page confirms standstill through the group whose
motion_joints are its own trajectory controller's joints (ELECTRI-237)."""

from pathlib import Path
import sys
from types import SimpleNamespace as NS

from rcl_interfaces.msg import ParameterValue
from rcl_interfaces.srv import GetParameters

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integ_operator_web.arm.ros_bridge import RosBridge

ARMS = ("right_joint1", "left_joint1", "updown")


def strings(*values):
    return ParameterValue(type=9, string_array_value=list(values))


def bridge(joint_names=ARMS):
    created = []
    evidence = NS(confirmed=[], confirm_standstill=lambda ok, at: evidence.confirmed.append(ok))
    b = NS(
        _manager="enable_manager",
        _motion_groups=(),
        _standstill_group="",
        _group=None,
        console=NS(joint_names=joint_names),
        _readback=NS(evidence=evidence, pending=None, standstill_client=None, motion_joints=()),
        create_client=lambda kind, name, **_: created.append(name) or NS(name=name),
    )
    return b, created


def receive(b, groups, *values):
    RosBridge._received_standstill_joints(b, groups, GetParameters.Response(values=list(values)))


def test_the_group_with_the_page_joints_provides_the_standstill_service():
    b, created = bridge()
    # First answer: only the group names are known.
    receive(b, (), strings("arms", "base"))
    assert b._motion_groups == ("arms", "base") and b._readback.motion_joints == ()
    receive(b, ("arms", "base"), strings("arms", "base"), strings(*ARMS), strings("steer1", "wheel1"))
    assert created == ["/enable_manager/arms/confirm_standstill"]
    assert b._readback.motion_joints == ARMS
    # The same answer again keeps the client.
    receive(b, ("arms", "base"), strings("arms", "base"), strings(*ARMS), strings("steer1", "wheel1"))
    assert created == ["/enable_manager/arms/confirm_standstill"]


def test_no_matching_group_never_confirms_standstill():
    b, created = bridge(joint_names=("right_joint1", "left_joint1"))
    receive(b, ("arms",), strings("arms"), strings(*ARMS))
    assert created == [] and b._readback.standstill_client is None
    assert b._readback.motion_joints == ()


def test_a_malformed_answer_clears_the_scope():
    b, _ = bridge()
    b._readback.motion_joints = ARMS
    receive(b, ("arms",), strings("arms"))
    assert b._readback.motion_joints == ()
