"""The web is a publisher on the chassis velocity topic only while it holds chassis control.

Navigation does not allow a second publisher on that topic (N-04), so an idle web must not have one.
"""

from pathlib import Path
import sys
import time

import rclpy
from rclpy.executors import SingleThreadedExecutor

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integ_operator_web.node import OperatorWebNode  # noqa: E402


def wait_until(executor, condition, timeout=5.0):
    deadline = time.monotonic() + timeout
    while not condition() and time.monotonic() < deadline:
        executor.spin_once(timeout_sec=0.02)
    return condition()


def test_publisher_exists_only_while_the_web_holds_control():
    rclpy.init()
    try:
        web = OperatorWebNode()
        web.backend.allowed = lambda: True  # an enabled chassis with a velocity subscriber
        observer = rclpy.create_node("navigation_observer")
        topic = web.config.command_topic
        executor = SingleThreadedExecutor()
        executor.add_node(web)
        executor.add_node(observer)

        def publishers():
            return observer.count_publishers(topic)

        executor.spin_once(timeout_sec=0.2)
        assert publishers() == 0

        web.arbiter.acquire("operator")
        assert wait_until(executor, lambda: publishers() == 1)

        web.arbiter.release("operator")
        assert wait_until(executor, lambda: publishers() == 0)
    finally:
        rclpy.shutdown()


def test_no_publisher_while_the_chassis_does_not_accept_commands():
    rclpy.init()
    try:
        web = OperatorWebNode()
        web.backend.allowed = lambda: False  # e.g. chassis disabled
        observer = rclpy.create_node("navigation_observer")
        executor = SingleThreadedExecutor()
        executor.add_node(web)
        executor.add_node(observer)

        web.arbiter.acquire("operator")
        assert not wait_until(
            executor, lambda: observer.count_publishers(web.config.command_topic) > 0, timeout=1.0
        )
    finally:
        rclpy.shutdown()
