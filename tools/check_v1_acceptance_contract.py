#!/usr/bin/env python3
"""Release-acceptance coverage guard; never treats simulated tests as live evidence.

Normal CTest mode checks that the tests for currently agreed V1 behaviours still
exist and assert their critical conditions. --release-gate is a separate,
explicit decision tool requiring sanitised manual evidence. It is intentionally
NOT registered with CTest because physical/live validation requires consent.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Actual test entry points from the runtime CMake, not documentation-only examples.
CTEST_NAMES = (
    'accloud_ui_qml', 'accloud_ui_qml_upload',
    'accloud_har_import', 'accloud_direct_print_lifecycle',
    'accloud_direct_print_preparation', 'accloud_mqtt_flow',
    'accloud_viewer_controls', 'accloud_render3d_shader_compile',
    'accloud_security_redaction', 'accloud_release_candidate_contract',
)

# Test names are the Qt QuickTest methods actually executed by accloud_ui_qml.
CONTROL_ROOM_TESTS = {
    'test_main_menu_is_grouped_settings_session_help': (),
    'test_about_identity_and_source_link': ('github.com/MolgoVulgo',),
    'test_session_dialog_skip_does_not_commit_or_persist': (),
    'test_session_dialog_unverified_cloud_is_not_marked_active': (),
    'test_printer_functions_card_visibility_and_feeding_modal_ui': (),
    'test_cloud_files_batch_delete_uses_workflow_bridge_sequential_result': (),
    'test_file_card_shows_viewer_button_only_for_pwsz_in_viewer_build': (),
    'test_main_window_print_intent_routes_from_files_to_printers': (
        'sendPrintCalls', 'compare(String(printerPage.selectedPrinterLiveSnapshot.state), "READY")',
        'compare(printerPage.selectedPrinterLiveSnapshot.awaitingPrinterTelemetry, true)',
        'compare(Number(printerPage.liveProjectData.printStatus), -1)',
    ),
    'test_printer_order_http_acceptance_is_not_mqtt_printing': (
        'compare(String(snapshot.state), "READY")',
        'compare(snapshot.awaitingPrinterTelemetry, true)',
        'compare(String(panel.printerSemanticStatus()), "ORDER_PENDING")',
        'compare(String(panel.printerSemanticStatus()), "OFFLINE")',
        'compare(String(panel.printerSemanticStatus()), "ERROR")',
        'compare(String(snapshot.state), "PRINTING")',
        'compare(Number(page.liveProjectData.printStatus), -1)',
    ),
    'test_failed_direct_print_cleanup_uses_semantic_workflow_notices': (),
    'test_vertical_layer_range_wheel_moves_only_upper_handle': (),
}
UPLOAD_TESTS = (
    'test_download_dialog_uses_app_ui_and_prefills_cloud_file_name',
    'test_upload_finished_processing_sets_warn',
    'test_upload_finished_zero_gcode_stays_processing',
    'test_upload_finished_local_replacement_failure_sets_warn',
    'test_incomplete_inventory_is_visible_to_user',
    'test_toolbar_distinguishes_cloud_upload_and_direct_print',
)
PREPARATION_TESTS = (
    'testReadinessMustBeExactAndConfirmed',
    'testPrinterRecheckAndDispatchReservation',
    'testLostResponseCannotRetry',
    'testCancellationAndRestart',
    'testCorrelatedMqttResults',
)

# Every value must be a human-confirmed, non-secret status, never an invented result.
RELEASE_EVIDENCE = (
    'local_full_non_live',
    'qt_lupdate_lrelease_audit',
    'har_startup_skip_restart',
    'cloud_upload_download_delete',
    'printer_http_mqtt_confirmation',
    'deferred_direct_print_readiness',
    'deferred_direct_print_restart_no_duplicate',
    'printer_and_cloud_cleanup',
    'pwsz_viewer_runtime',
    'desktop_1920x1080_fr_en',
    'desktop_scaling_125_150',
    'security_and_cache_recovery',
    'prod_build_authorized_and_passed',
    'real_cloud_m7_pro_authorized_and_passed',
    'final_release_approval',
)


def has_ctest(cmake: str, name: str) -> bool:
    return re.search(r'add_test\s*\(\s*(?:NAME\s+)?' + re.escape(name) + r'\b', cmake) is not None


def test_bodies(qml: str) -> dict[str, str]:
    matches = list(re.finditer(r'\bfunction\s+(test_[A-Za-z0-9_]+)\s*\(', qml))
    return {m.group(1): qml[m.start():matches[i+1].start() if i+1 < len(matches) else len(qml)]
            for i, m in enumerate(matches)}


def cpp_runs_test(code: str, name: str) -> bool:
    definition = re.search(r'\bvoid\s+' + re.escape(name) + r'\s*\(', code)
    main = re.search(r'\bint\s+main\s*\(', code)
    return bool(definition and main and re.search(r'\b' + re.escape(name) + r'\s*\(', code[main.end():]))


def check(root: Path) -> list[str]:
    errors = []
    paths = {
        'cmake': 'accloud/CMakeLists.txt',
        'control': 'tests/ui/qml/tst_control_room.qml',
        'upload': 'tests/ui/qml/tst_cloud_files_upload.qml',
        'preparation': 'tests/printing/test_direct_print_preparation.cpp',
    }
    source = {}
    for key, relative in paths.items():
        try:
            source[key] = (root / relative).read_text(encoding='utf-8')
        except OSError as exc:
            errors.append(f'missing test contract source: {relative}: {type(exc).__name__}')
    if errors:
        return errors
    cmake = source['cmake']
    for name in CTEST_NAMES + ('accloud_v1_acceptance_contract',):
        if not has_ctest(cmake, name):
            errors.append(f'CTest no longer registers {name}')
    if 'check_v1_acceptance_contract.py' not in cmake:
        errors.append('CTest acceptance guard script is not wired')
    control = test_bodies(source['control'])
    upload = test_bodies(source['upload'])
    for name, tokens in CONTROL_ROOM_TESTS.items():
        body = control.get(name)
        if not body:
            errors.append(f'control-room QML scenario missing: {name}')
            continue
        for token in tokens:
            if token not in body:
                errors.append(f'control-room QML scenario {name} no longer asserts {token!r}')
    for name in UPLOAD_TESTS:
        if not upload.get(name):
            errors.append(f'upload QML scenario missing: {name}')
    for name in PREPARATION_TESTS:
        if not cpp_runs_test(source['preparation'], name):
            errors.append(f'preparation C++ scenario not executed in main(): {name}')
    if 'accloud_direct_print_preparation' not in cmake:
        errors.append('deferred preparation unit test disappeared')
    return errors


def deferred_runtime_has_wiring(root: Path) -> bool:
    # Conservative indicator ONLY. One reference cannot prove correct exactly-once
    # behaviour. Absence does prove the isolated policy is not wired to the runtime.
    candidates = [root/'src/accloud/app/PrintWorkflowBridge.cpp',
                  root/'src/accloud/app/PrintWorkflowBridge.h']
    paths = root/'src/accloud/app/usecases/printing'
    if paths.is_dir():
        candidates.extend(p for p in paths.glob('*.cpp'))
        candidates.extend(p for p in paths.glob('*.h')
                          if p.name != 'DirectPrintPreparationPolicy.h')
    use = re.compile(r'\b(?:DirectPrintPreparationPolicy|reserveDirectPrintDispatch|directReservationPersisted|recoverDirectPreparation)\b')
    return any(use.search(p.read_text(encoding='utf-8'))
               for p in candidates if p.is_file())


def evaluate_evidence(raw: object) -> list[str]:
    if not isinstance(raw, dict):
        return ['evidence must be a JSON object of explicit statuses']
    issues = []
    extra = sorted(set(raw)-set(RELEASE_EVIDENCE))
    if extra:
        issues.append('unknown evidence keys: ' + ', '.join(extra))
    for key in RELEASE_EVIDENCE:
        value = raw.get(key, 'not_tested')
        if value not in ('passed', 'failed', 'not_tested', 'blocked'):
            issues.append(f'{key}: invalid status (passed/failed/not_tested/blocked only)')
        elif value != 'passed':
            issues.append(f'{key}: {value}')
    return issues


def self_test() -> None:
    assert has_ctest('add_test(NAME accloud_ui_qml COMMAND foo)', 'accloud_ui_qml')
    assert has_ctest('add_test(accloud_har_import foo)', 'accloud_har_import')
    assert not has_ctest('add_test(NAME accloud_ui_qml_upload COMMAND foo)', 'accloud_ui_qml')
    cases = test_bodies('function test_alpha() { compare(x, "READY") }\nfunction test_beta() { verify(y) }')
    assert '"READY"' in cases['test_alpha'] and 'verify(y)' not in cases['test_alpha']
    assert cpp_runs_test('void testOne() {} int main() { testOne(); }', 'testOne')
    assert not cpp_runs_test('void testOne() {} int main() { }', 'testOne')
    assert len(evaluate_evidence({})) == len(RELEASE_EVIDENCE)
    assert evaluate_evidence({k: 'passed' for k in RELEASE_EVIDENCE}) == []
    assert evaluate_evidence({**{k: 'passed' for k in RELEASE_EVIDENCE}, 'password': 'xx'})
    print('V1 acceptance checker self-test: OK')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--release-gate', type=Path, metavar='SANITIZED_EVIDENCE_JSON',
                        help='explicit final-release check; NOT part of CTest')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = check(args.repo_root)
    if errors:
        for error in errors:
            print('V1 acceptance CONTRACT FAIL: ' + error, file=sys.stderr)
        return 1
    print(f'V1 acceptance test contracts: OK ({len(CTEST_NAMES)} CTest owners, '
          f'{len(CONTROL_ROOM_TESTS)+len(UPLOAD_TESTS)+len(PREPARATION_TESTS)} critical scenarios)')
    if args.release_gate is None:
        print('Release verdict: NOT ASSESSED (manual/live evidence not supplied)')
        return 0
    try:
        raw = json.loads(args.release_gate.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        raw = {}
    gaps = evaluate_evidence(raw)
    if not deferred_runtime_has_wiring(args.repo_root):
        gaps.append('deferred direct-print safety policy is not connected to the active C++ workflow')
    if gaps:
        for gap in gaps:
            print('RELEASE BLOCKED: ' + gap)
        return 1
    print('Release evidence gate: ALL ITEMS PRESENT; human publication decision still required')
    return 0


if __name__ == '__main__':
    sys.exit(main())
