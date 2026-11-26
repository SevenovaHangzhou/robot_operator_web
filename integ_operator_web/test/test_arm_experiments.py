"""The browser selects a stored package; it cannot supply motion targets through this command."""
from types import SimpleNamespace
import pytest
from integ_operator_web.arm.page import ArmPage


def test_transfer_disabled_and_no_inline_targets():
    page = SimpleNamespace(console=object(), experiment_receiver=None)
    with pytest.raises(ValueError, match='未配置'):
        ArmPage._command(page, 'run_experiment_package', 'session', {'package_id':'p','request_id':'r'})
    calls = []
    page.experiment_receiver = SimpleNamespace(start=lambda *args: calls.append(args))
    with pytest.raises(ValueError, match='只接受'):
        ArmPage._command(page, 'run_experiment_package', 'session', {'package_id':'p','request_id':'r','target':{'joint':0}})
    assert not calls
    ArmPage._command(page, 'run_experiment_package', 'session', {'package_id':'p','request_id':'r'})
    assert calls == [('session','p','r')]


def test_run_sequence_cannot_supply_a_workflow_observer():
    calls = []
    page = SimpleNamespace(console=SimpleNamespace(run_sequence=lambda *a, **kw: calls.append((a,kw))))
    ArmPage._command(page,'run_sequence','session',{'steps':[], '_workflow':{'passed':True}})
    assert '_workflow' not in calls[0][1]
