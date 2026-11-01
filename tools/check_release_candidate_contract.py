#!/usr/bin/env python3
"""V1 candidate contract: active QML strings, current status tests and release identity.

This is a deterministic, targeted *supplement* to Qt lupdate, not a replacement
for the full translator extraction run on the local Qt development machine.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

QML_CONTEXT_FILES = {
    "MainWindow": "src/accloud/ui/qml/MainWindow.qml",
    "SessionSettingsDialog": "src/accloud/ui/qml/dialogs/SessionSettingsDialog.qml",
    "CloudFilesPage": "src/accloud/ui/qml/pages/CloudFilesPage.qml",
    "CloudFileDetailsDialog": "src/accloud/ui/qml/pages/CloudFileDetailsDialog.qml",
    "PrinterPage": "src/accloud/ui/qml/pages/PrinterPage.qml",
    "PrinterDetailPanel": "src/accloud/ui/qml/pages/PrinterDetailPanel.qml",
    "PrinterRemotePrintConfigDialog": "src/accloud/ui/qml/pages/PrinterRemotePrintConfigDialog.qml",
}
LITERAL_QSTR = re.compile(r'qsTr\s*\(\s*"((?:\\.|[^"\\])*)"')


def extract_qstr(text: str) -> set[str]:
    result = set()
    for match in LITERAL_QSTR.finditer(text):
        raw = match.group(1)
        try:
            source = json.loads('"' + raw + '"')
        except json.JSONDecodeError:
            source = raw
        if source:
            result.add(source)
    return result


def catalog(path: Path) -> dict[str, dict[str, ET.Element]]:
    root = ET.parse(path).getroot()
    assert root.tag == 'TS', str(path)
    return {
        c.findtext('name'): {m.findtext('source'): m for m in c.findall('message')}
        for c in root.findall('context')
    }


def function_body(code: str, function: str) -> str:
    m = re.search(r"\bfunction\s+" + re.escape(function) + r"\s*\([^)]*\)\s*\{", code)
    if not m:
        return ""
    depth = 1
    i = m.end()
    start = i
    while i < len(code) and depth:
        if code[i] == '{':
            depth += 1
        elif code[i] == '}':
            depth -= 1
        i += 1
    return code[start:i - 1] if depth == 0 else ""


def check(root: Path) -> list[str]:
    errors = []
    paths = {k: root / v for k, v in QML_CONTEXT_FILES.items()}
    tables = {lang: catalog(root / f'i18n/accloud_{lang}.ts') for lang in ('fr', 'en')}
    for context, path in paths.items():
        sources = extract_qstr(path.read_text(encoding='utf-8'))
        for lang, table in tables.items():
            messages = table.get(context, {})
            for source in sorted(sources):
                if source not in messages:
                    errors.append(f'{lang} missing {context}: {source!r}')
                elif lang == 'fr':
                    trans = messages[source].find('translation')
                    if trans is None or not (trans.text or '').strip() or trans.get('type') == 'unfinished':
                        errors.append(f'fr untranslated {context}: {source!r}')
    cmake = (root / 'accloud/CMakeLists.txt').read_text(encoding='utf-8')
    if not re.search(r'project\(accloud\s+VERSION\s+1\.0\.0\b', cmake):
        errors.append('Project must remain accloud 1.0.0')
    if not re.search(r'set\(ACCLOUD_VERSION_PRERELEASE\s+"rc\.1"', cmake):
        errors.append('Candidate prerelease must remain rc.1 until approval')
    if 'ACCLOUD_DISPLAY_VERSION' not in cmake or 'ACCLOUD_APP_VERSION' not in cmake:
        errors.append('CMake candidate version propagation is missing')
    main = (root / 'src/accloud/ui/qml/MainWindow.qml').read_text(encoding='utf-8')
    bootstrap = (root / 'src/accloud/app/main.cpp').read_text(encoding='utf-8')
    for token in ('text: "accloud"', 'Qt.application.version',
                  'https://github.com/MolgoVulgo/anycubic-cloud-manager',
                  'Not affiliated with or endorsed by Anycubic.'):
        if token not in main:
            errors.append(f'About identity contract missing: {token}')
    if 'setApplicationVersion(QStringLiteral(ACCLOUD_APP_VERSION))' not in bootstrap:
        errors.append('Desktop does not forward CMake candidate version')
    for filename in ('readme.md', 'readme-FR.md', 'CHANGELOG.md'):
        content = (root / filename).read_text(encoding='utf-8')
        if '1.0.0-rc.1' not in content:
            errors.append(f'{filename} omits release candidate version')
    changelog = (root / 'CHANGELOG.md').read_text(encoding='utf-8')
    if 'Unreleased' not in changelog:
        errors.append('Changelog must mark candidate as unreleased')
    tests = (root / 'tests/ui/qml/tst_control_room.qml').read_text(encoding='utf-8')
    specific = function_body(tests, 'test_printer_order_http_acceptance_is_not_mqtt_printing')
    routed = function_body(tests, 'test_main_window_print_intent_routes_from_files_to_printers')
    for name, body in [('telemetry', specific), ('routed print', routed)]:
        if not body or 'awaitingPrinterTelemetry' not in body or 'printStatus' not in body:
            errors.append(f'{name} QML regression test lacks pending telemetry assertions')
    if 'compare(String(printerPage.selectedPrinterLiveSnapshot.state), "READY")' not in routed:
        errors.append('Routed print QML test has stale expected printer state')
    if 'compare(String(printerPage.selectedPrinterLiveSnapshot.state), "READY")' not in routed:
        errors.append('Routed print QML test has stale expected printer state')
    if 'compare(Number(printerPage.liveProjectData.printStatus), -1)' not in routed:
        errors.append('Routed print QML test still assumes HTTP-accepted == active printing')
    if 'compare(String(snapshot.state), "READY")' not in specific:
        errors.append('Telemetry QML test does not preserve real READY state')
    # Mandatory evidence limitation: the policy remains unconnected to the active flow.
    for filename in ('docs/05-qml-ui.md', 'docs/FR/05-interface-qml.md'):
        text = (root / filename).read_text(encoding='utf-8')
        if 'DirectPrintPreparationPolicy.h' not in text:
            errors.append(f'{filename} lost deferred-print integration limitation')
    for filename in ('packaging/desktop/org.accloud.App.desktop', 'packaging/arch/accloud.desktop'):
        if 'Name=accloud' not in (root / filename).read_text(encoding='utf-8'):
            errors.append(f'{filename} has stale public application name')
    metadata = (root / 'packaging/org.accloud.App.metainfo.xml').read_text(encoding='utf-8')
    if '<name>accloud</name>' not in metadata or 'github.com/MolgoVulgo/anycubic-cloud-manager</url>' not in metadata:
        errors.append('AppStream metadata has stale public identity/homepage')
    # Arch packaging is maintained independently from the candidate runtime.
    arch = (root / 'packaging/arch/PKGBUILD').read_text(encoding='utf-8')
    if 'cp -r' in arch and '/resources' in arch:
        errors.append('Arch package must not copy bundled TLS private material')
    if 'org.accloud.App.png' not in arch or not (root / 'packaging/arch/acm.png').is_file():
        errors.append('Arch package is missing its desktop icon')
    return errors


def self_test() -> None:
    assert extract_qstr('text: qsTr("Hello")') == {'Hello'}
    assert extract_qstr('text: qsTr("Line\\nnext")') == {'Line\nnext'}
    assert extract_qstr('not_tr("Ignore")') == set()
    body = function_body('function fn() { if (true) { ok() } }', 'fn')
    assert 'ok()' in body
    assert not function_body('function other() { }', 'fn')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print('Candidate checker self-test: OK')
        return 0
    problems = check(args.repo_root.resolve())
    if problems:
        print('Release candidate contract: FAILED')
        print('\n'.join('- ' + issue for issue in problems))
        return 1
    print('Release candidate contract: OK (FR/EN QML messages, identity and status tests)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
