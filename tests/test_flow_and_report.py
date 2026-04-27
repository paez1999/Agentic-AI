from src.reporting.formatter import format_final_markdown_report
from src.tasks.definitions import FlowInput, run_sequential_flow


def test_sequential_flow_returns_outputs_for_all_tasks():
    result = run_sequential_flow(FlowInput())
    assert "task_1_monitor_output" in result
    assert "task_2_inventory_output" in result
    assert "task_3_route_output" in result


def test_markdown_report_contains_authorization_prompt():
    result = run_sequential_flow(FlowInput())
    report = format_final_markdown_report(result)
    assert "Opcion A" in report
    assert "Opcion B" in report
    assert "Solicitud de Autorizacion" in report
