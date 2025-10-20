from src.agent.system_manager import SystemManager


def test_system_manager_init():
    sm = SystemManager()
    assert hasattr(sm, 'allowed_commands')


def test_check_op_flag():
    sm = SystemManager()
    assert isinstance(sm.op_available, bool)
