from src.agent.an_agent import process_system_command
from src.agent.system_manager import SystemManager


def test_process_unknown_command():
    sm = SystemManager()
    res = process_system_command("comando invalido", sm)
    assert "OUTPUT_EXECUTIVO" in res
