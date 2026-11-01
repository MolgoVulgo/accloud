#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import re
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "accloud"
QML_ROOT = SRC_ROOT / "ui" / "qml"
APP_ROOT = SRC_ROOT / "app"


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def check_worker_ratio_combo_mapping(main_qml: str) -> list[str]:
    """Guard the actual combo callback, not an obsolete index-to-ratio shortcut.

    Worker ratios may collapse to a single visible option on small machines,
    and a custom saved count may add an extra row. Consequently the combo
    index is not necessarily the persisted ratio.
    """
    issues: list[str] = []
    match = re.search(
        r"AppComboBox\s*\{\s*id:\s*settingsWorkerRatioCombo\b"
        r"(?P<body>.*?)^\s{16}\}\s*$",
        main_qml,
        flags=re.DOTALL | re.MULTILINE,
    )
    if match is None:
        return ["MainWindow worker ratio selector block is missing"]

    body = match.group("body")
    for required in (
        "model: root.workerDisplayOptions()",
        "var options = root.workerDisplayOptions()",
        "index < 0 || index >= options.length || options[index].value === 0",
        "root.persistRender3dWorkerRatio(options[index].value)",
        "root.workerOptionIndexForRatio(options[index].value)",
    ):
        if required not in body:
            issues.append(f"MainWindow worker ratio selector mapping missing `{required}`")
    if "root.persistRender3dWorkerRatio(index + 1)" in body:
        issues.append("MainWindow worker ratio selector must not derive ratio from combo index")
    return issues


def find_raw_dialogs() -> list[pathlib.Path]:
    offenders: list[pathlib.Path] = []
    for path in QML_ROOT.rglob("*.qml"):
        if path.name == "AppDialogFrame.qml":
            continue
        text = read_text(path)
        if re.search(r"^\s*Dialog\s*\{", text, flags=re.MULTILINE):
            offenders.append(path)
    return offenders


def has_tab_property(path: pathlib.Path, object_id: str, expression: str) -> bool:
    text = read_text(path)
    pattern = (
        r"AppTabBar\s*\{"
        r"(?:(?!AppTabBar\s*\{).)*?"
        + re.escape(f"id: {object_id}")
        + r"(?:(?!\}).)*?"
        + re.escape(expression)
    )
    return re.search(pattern, text, flags=re.DOTALL) is not None


def has_tab_setting(path: pathlib.Path, object_id: str, key: str, value: str) -> bool:
    return has_tab_property(path, object_id, f'{key}: "{value}"')


def has_object_property(path: pathlib.Path, object_type: str, object_id: str, expression: str) -> bool:
    text = read_text(path)
    pattern = (
        re.escape(object_type)
        + r"\s*\{"
        + r"(?:(?!\}).)*?"
        + re.escape(f"id: {object_id}")
        + r"(?:(?!\}).)*?"
        + re.escape(expression)
    )
    return re.search(pattern, text, flags=re.DOTALL) is not None


def check_tabs_config() -> list[str]:
    issues: list[str] = []

    main_window = QML_ROOT / "MainWindow.qml"
    if not has_tab_setting(main_window, "controlTabs", "tabVariant", "navigation"):
        issues.append("MainWindow controlTabs missing `tabVariant: \"navigation\"`")
    if not has_tab_setting(main_window, "controlTabs", "tabSizingMode", "content"):
        issues.append("MainWindow controlTabs missing `tabSizingMode: \"content\"`")
    if not has_tab_property(main_window, "controlTabs", "minTabWidth: 120"):
        issues.append("MainWindow controlTabs missing `minTabWidth: 120`")
    if not has_tab_property(main_window, "controlTabs", 'inactiveColor: "transparent"'):
        issues.append("MainWindow controlTabs missing transparent inactive background")
    if not has_tab_property(main_window, "controlTabs", 'stripColor: "transparent"'):
        issues.append("MainWindow controlTabs missing transparent strip background")

    printers_tabs = QML_ROOT / "pages" / "PrintersTabsBar.qml"
    printers_text = read_text(printers_tabs)
    if 'tabVariant: "local"' not in printers_text:
        issues.append("PrintersTabsBar missing `tabVariant: \"local\"`")
    if 'tabSizingMode: "content"' not in printers_text:
        issues.append("PrintersTabsBar missing `tabSizingMode: \"content\"`")

    cloud_details = QML_ROOT / "pages" / "CloudFileDetailsDialog.qml"
    if not has_tab_setting(cloud_details, "detailsTabBar", "tabVariant", "local"):
        issues.append("CloudFileDetailsDialog detailsTabBar missing `tabVariant: \"local\"`")
    if not has_tab_setting(cloud_details, "detailsTabBar", "tabSizingMode", "content"):
        issues.append("CloudFileDetailsDialog detailsTabBar missing `tabSizingMode: \"content\"`")

    return issues


def check_tabs_geometry_v2() -> list[str]:
    issues: list[str] = []

    app_page_frame = QML_ROOT / "components" / "AppPageFrame.qml"
    app_page_frame_text = read_text(app_page_frame)
    if "property bool embeddedInTabsContainer: false" not in app_page_frame_text:
        issues.append("AppPageFrame missing `embeddedInTabsContainer` property")
    if "radius: embeddedInTabsContainer ? 0 : Theme.radiusDialog" not in app_page_frame_text:
        issues.append("AppPageFrame missing conditional radius for embedded tabs container")
    if "border.width: embeddedInTabsContainer ? 0 : Theme.borderWidth" not in app_page_frame_text:
        issues.append("AppPageFrame missing conditional border width for embedded tabs container")

    main_window = QML_ROOT / "MainWindow.qml"
    main_text = read_text(main_window)

    menu_order = (
        'objectName: "menuSession"',
        'objectName: "menuParametre"',
        'objectName: "menuHelp"',
    )
    menu_positions = [main_text.find(token) for token in menu_order]
    if any(position < 0 for position in menu_positions) or menu_positions != sorted(menu_positions):
        issues.append("MainWindow top menu must remain ordered Session -> Settings -> Help")
    for required_inline in (
        'objectName: "settingsThemePresetCombo"',
        'objectName: "settingsAccentPresetCombo"',
        'objectName: "settingsLanguageCombo"',
        'objectName: "settingsRender3dPaletteCombo"',
        'objectName: "settingsRender3dPalettePreviewPart"',
    ):
        if required_inline not in main_text:
            issues.append(f"MainWindow inline preferences missing {required_inline}")
    for obsolete_dialog in ('id: themeDialog', 'id: languageDialog',
                            'id: render3dPaletteDialog'):
        if obsolete_dialog in main_text:
            issues.append(f"MainWindow must not reopen nested preferences: {obsolete_dialog}")
    for required in (
        'objectName: "menuSettingsOpen"',
        'objectName: "settingsDialog"',
        'objectName: "settingsTechnicalDetailsCheckBox"',
        'objectName: "settingsDirectDeleteLocalOnFailureCheckBox"',
        'objectName: "settingsPwszPreviewCompletionCheckBox"',
        'objectName: "settingsPwszPreviewConfirmationCheckBox"',
        'objectName: "settingsWorkerRatioCombo"',
        'objectName: "menuSessionImportHar"',
        'objectName: "menuHelpAbout"',
        "property bool viewer3dEnabled:",
        "viewerEnabled: root.viewer3dEnabled",
    ):
        if required not in main_text:
            issues.append(f"MainWindow menu/viewer contract missing `{required}`")
    issues.extend(check_worker_ratio_combo_mapping(main_text))
    for forbidden in (
        'objectName: "menuSettingsSession"',
        'objectName: "menuSettingsInterface"',
        'objectName: "menuSettingsPrinting"',
        'objectName: "menuSettingsFilesUpload"',
        'objectName: "menuSettingsViewer3d"',
        'objectName: "render3dWorkersSpin"',
        'objectName: "menuSettingsMqttAuthMode"',
        'objectName: "menuSessionLocation"',
        'objectName: "menuSessionDetails"',
        'objectName: "menuHelpGit"',
        "experimentalViewerEnabled",
    ):
        if forbidden in main_text:
            issues.append(f"MainWindow obsolete menu/viewer token remains `{forbidden}`")
    for required in (
        "anchors.margins: 0",
        "spacing: 0",
        "embeddedInTabsContainer: true",
        'inactiveColor: "transparent"',
        'stripColor: "transparent"',
        "tabTopCornerRadius: Theme.radiusControl",
    ):
        if required not in main_text:
            issues.append(f"MainWindow tabsPanel missing `{required}`")

    if not has_object_property(main_window, "Rectangle", "tabsPanel", 'color: "transparent"'):
        issues.append("MainWindow tabsPanel missing transparent background")
    for required in (
        "Layout.leftMargin: Theme.borderWidth",
        "Layout.rightMargin: Theme.borderWidth",
        "Layout.bottomMargin: Theme.borderWidth",
    ):
        if not has_object_property(main_window, "StackLayout", "controlRoomStack", required):
            issues.append(f"MainWindow controlRoomStack missing `{required}`")

    cloud_files_page = QML_ROOT / "pages" / "CloudFilesPage.qml"
    cloud_text = read_text(cloud_files_page)
    if "property bool embeddedInTabsContainer: false" not in cloud_text:
        issues.append("CloudFilesPage missing `embeddedInTabsContainer` property")
    if "embeddedInTabsContainer: root.embeddedInTabsContainer" not in cloud_text:
        issues.append("CloudFilesPage pageFrame missing embedded propagation")
    if "readonly property int tableRowHorizontalMargin: 12" not in cloud_text:
        issues.append("CloudFilesPage missing coherent 12 px table side inset")
    if "scrollbarReserve: root.tableScrollbarReserve" not in cloud_text:
        issues.append("CloudFilesPage missing stable scrollbar reserve propagation")

    cloud_toolbar = QML_ROOT / "pages" / "CloudFilesToolbar.qml"
    toolbar_text = read_text(cloud_toolbar)
    for required in (
        'objectName: "filesPrimaryActionsHost"',
        'objectName: "filesPrimaryActions"',
        'objectName: "deleteSelectedFilesButton"',
        "visible: root.selectedFilesCount > 0 || root.batchDeleteRunning",
        "anchors.centerIn: parent",
    ):
        if required not in toolbar_text:
            issues.append(f"CloudFilesToolbar missing `{required}`")

    cloud_table_panel = QML_ROOT / "pages" / "CloudFilesTablePanel.qml"
    table_panel_text = read_text(cloud_table_panel)
    for required in (
        'objectName: "filesTablePanel"',
        "border.width: Theme.borderWidth",
        "Layout.leftMargin: root.tableRowHorizontalMargin",
        "Layout.rightMargin: root.tableRowHorizontalMargin",
        "horizontalMargin: root.tableRowHorizontalMargin",
        "signal fileSelectionToggled(string fileId, string fileName, bool checked)",
    ):
        if required not in table_panel_text:
            issues.append(f"CloudFilesTablePanel missing `{required}`")

    cloud_table_row = QML_ROOT / "pages" / "CloudFilesTableRow.qml"
    table_row_text = read_text(cloud_table_row)
    for required in (
        'objectName: "fileRowSelectionCheckBox"',
        "property bool batchSelected: false",
        "signal selectionToggled(string fileId, string fileName, bool checked)",
    ):
        if required not in table_row_text:
            issues.append(f"CloudFilesTableRow missing `{required}`")

    for required in (
        "property var selectedFiles: []",
        "readonly property int selectedFilesCount: selectedFiles.length",
        "function startBatchDelete()",
        "cloudFilesWorkflowBridge.startBatchDelete(selectedFiles)",
        "id: batchDeleteConfirmDialog",
        "onDeleteSelectedRequested: root.requestDeleteSelected()",
    ):
        if required not in cloud_text:
            issues.append(f"CloudFilesPage missing `{required}`")

    printer_page = QML_ROOT / "pages" / "PrinterPage.qml"
    printer_page_text = read_text(printer_page)
    if "property bool embeddedInTabsContainer: false" not in printer_page_text:
        issues.append("PrinterPage missing `embeddedInTabsContainer` property")
    if "embeddedInTabsContainer: root.embeddedInTabsContainer" not in printer_page_text:
        issues.append("PrinterPage missing embedded propagation to PrinterMainPanel")

    printer_main_panel = QML_ROOT / "pages" / "PrinterMainPanel.qml"
    printer_main_text = read_text(printer_main_panel)
    for required in (
        "id: printerTabsContainer",
        "spacing: 0",
        "embeddedInTabsContainer: true",
    ):
        if required not in printer_main_text:
            issues.append(f"PrinterMainPanel missing `{required}` for unified tabs container")

    printers_tabs = QML_ROOT / "pages" / "PrintersTabsBar.qml"
    printers_tabs_text = read_text(printers_tabs)
    for required in (
        "property bool embeddedInTabsContainer: false",
        "radius: embeddedInTabsContainer ? 0 : Theme.radiusControl",
        "border.width: embeddedInTabsContainer ? 0 : Theme.borderWidth",
        "tabTopCornerRadius: embeddedInTabsContainer ? Theme.radiusControl : root.radius",
    ):
        if required not in printers_tabs_text:
            issues.append(f"PrintersTabsBar missing `{required}`")

    printer_details = QML_ROOT / "pages" / "PrinterDetailPanel.qml"
    printer_details_text = read_text(printer_details)
    for required in (
        "property bool embeddedInTabsContainer: false",
        "radius: embeddedInTabsContainer ? 0 : Theme.radiusControl",
        "border.width: embeddedInTabsContainer ? 0 : Theme.borderWidth",
    ):
        if required not in printer_details_text:
            issues.append(f"PrinterDetailPanel missing `{required}`")

    cloud_details = QML_ROOT / "pages" / "CloudFileDetailsDialog.qml"
    cloud_details_text = read_text(cloud_details)
    for required in (
        "id: detailsTabsContainer",
        "spacing: 0",
        "stripColor: Theme.bgDialog",
        "tabTopCornerRadius: detailsTabsContainer.radius",
    ):
        if required not in cloud_details_text:
            issues.append(f"CloudFileDetailsDialog missing `{required}`")

    app_tab_bar = QML_ROOT / "components" / "AppTabBar.qml"
    app_tab_bar_text = read_text(app_tab_bar)
    for required in (
        "property int tabTopCornerRadius:",
        "readonly property bool _hasActiveTab:",
        "width: root._hasActiveTab ? Math.max(0, root._activeTabLeft) : parent.width",
        "width: root._hasActiveTab ? Math.max(0, parent.width - root._activeTabRight) : 0",
    ):
        if required not in app_tab_bar_text:
            issues.append(f"AppTabBar missing v2 geometry rule `{required}`")

    app_tab_button = QML_ROOT / "components" / "AppTabButton.qml"
    app_tab_button_text = read_text(app_tab_button)
    for required in (
        "readonly property bool lastVisibleTab:",
        "readonly property int verticalBorderBottomMargin:",
        "id: tabStrokeCanvas",
        "ctx.arc(",
        "onLastVisibleTabChanged: tabStrokeCanvas.requestPaint()",
    ):
        if required not in app_tab_button_text:
            issues.append(f"AppTabButton missing v2 geometry rule `{required}`")

    return issues


def check_reactive_theme_contract() -> list[str]:
    issues: list[str] = []
    theme_qml = QML_ROOT / "components" / "Theme.qml"
    qmldir = QML_ROOT / "components" / "qmldir"
    resources = read_text(APP_ROOT / "resources.qrc")
    main = read_text(QML_ROOT / "MainWindow.qml")
    tests = read_text(REPO_ROOT / "tests/ui/qml/tst_control_room.qml")
    if not theme_qml.is_file() or not qmldir.is_file():
        return ["reactive Theme.qml singleton/qmldir is missing"]
    singleton = read_text(theme_qml)
    registrations = read_text(qmldir)
    if "singleton Theme 1.0 Theme.qml" not in registrations:
        issues.append("qmldir does not register reactive Theme singleton")
    for component in (QML_ROOT / "components").glob("*.qml"):
        if component.name == "Theme.qml":
            continue
        if f"{component.stem} 1.0 {component.name}" not in registrations:
            issues.append(f"qmldir hides pre-existing component {component.name}")
    for token in ('pragma Singleton', 'property string themeName:',
                  'property string accentName:', 'readonly property var paletteTokens:',
                  'readonly property var accentTokens:', 'readonly property color bgDialog:',
                  'readonly property color fgPrimary:', 'readonly property color accent:'):
        if token not in singleton:
            issues.append(f"reactive theme singleton missing {token}")
    for token in ('alias="qml/components/Theme.qml"', 'alias="qml/components/qmldir"'):
        if token not in resources:
            issues.append(f"resources.qrc missing {token}")
    for source in QML_ROOT.rglob("*.qml"):
        if source == theme_qml:
            continue
        text = read_text(source)
        if 'Theme.js" as Theme' in text:
            issues.append(f"non-reactive Theme.js import remains in {source.relative_to(REPO_ROOT)}")
        if "Theme." in text and 'import "components"' not in text and 'import "../components"' not in text and 'import "."' not in text:
            issues.append(f"Theme singleton not imported in {source.relative_to(REPO_ROOT)}")
    for token in ('Theme.setThemePreset(candidateTheme)',
                  'Theme.setAccent(candidateAccent)',
                  'root.persistedThemeName = Theme.themeName'):
        if token not in main:
            issues.append(f"main theme preference no longer updates shared singleton: {token}")
    for token in ('test_theme_and_accent_update_all_loaded_controls_without_reopening',
                  'normalizedColor(dialog.background.color)',
                  'normalizedColor(themeCombo.background.color)',
                  'normalizedColor(tabs.panelColor)',
                  'normalizedColor(themeCombo.background.border.color)',
                  'themeCombo.activated(darkIndex)'):
        if token not in tests:
            issues.append(f"QML reactive theme regression missing {token}")
    return issues


def check_tab_stroke_tokens() -> list[str]:
    issues: list[str] = []

    theme_js = QML_ROOT / "components" / "Theme.js"
    theme_text = read_text(theme_js)
    for required in (
        "var tabStrokeWidth = 1",
        "var tabStrokeColor =",
        "var tabBaselineColor =",
        "tabStrokeWidth = borderWidth",
        "tabStrokeColor = palette.borderDefault",
        "tabBaselineColor = palette.borderDefault",
    ):
        if required not in theme_text:
            issues.append(f"Theme.js missing tab stroke token `{required}`")

    app_tab_bar = QML_ROOT / "components" / "AppTabBar.qml"
    bar_text = read_text(app_tab_bar)
    for required in (
        "property color baselineColor: Theme.tabBaselineColor",
        "property int baselineWidth: Theme.tabStrokeWidth",
    ):
        if required not in bar_text:
            issues.append(f"AppTabBar missing token wiring `{required}`")

    app_tab_button = QML_ROOT / "components" / "AppTabButton.qml"
    button_text = read_text(app_tab_button)
    for required in (
        "readonly property int strokeWidth: Theme.tabStrokeWidth",
        "return Theme.tabStrokeColor",
    ):
        if required not in button_text:
            issues.append(f"AppTabButton missing token wiring `{required}`")

    return issues


def check_form_components() -> list[str]:
    issues: list[str] = []

    form_label = QML_ROOT / "components" / "FormLabel.qml"
    form_row = QML_ROOT / "components" / "FormRow.qml"
    if not form_label.exists():
        issues.append("FormLabel.qml missing")
    else:
        form_label_text = read_text(form_label)
        for required in (
            "font.pixelSize: Theme.fontBodyPx",
            "color: Theme.fgPrimary",
        ):
            if required not in form_label_text:
                issues.append(f"FormLabel missing `{required}`")

    if not form_row.exists():
        issues.append("FormRow.qml missing")
    else:
        form_row_text = read_text(form_row)
        for required in (
            "default property alias fieldData: fieldsRow.data",
            "FormLabel {",
            "spacing: Theme.gapRow",
        ):
            if required not in form_row_text:
                issues.append(f"FormRow missing `{required}`")

    for dialog in (
        QML_ROOT / "dialogs" / "PrintDraftDialog.qml",
        QML_ROOT / "dialogs" / "UploadDraftDialog.qml",
        QML_ROOT / "dialogs" / "SessionSettingsDialog.qml",
    ):
        text = read_text(dialog)
        if "FormRow {" not in text:
            issues.append(f"{dialog.relative_to(REPO_ROOT)} missing FormRow usage")

    return issues


def check_cloud_file_details_contract() -> list[str]:
    issues: list[str] = []
    details_dialog = QML_ROOT / "pages" / "CloudFileDetailsDialog.qml"
    cloud_files_page = QML_ROOT / "pages" / "CloudFilesPage.qml"
    main_window = QML_ROOT / "MainWindow.qml"

    details_text = read_text(details_dialog)
    for required in (
        'objectName: "cloudFileDetailsThumbnail"',
        'source: root.thumbnailSource()',
        'property bool showAdvancedDetails: false',
        'objectName: "cloudFileDetailsCompactSummaryCard"',
        'Layout.maximumHeight: 170',
        'Layout.minimumHeight: 300',
        'component DetailsPanel: Flickable {',
        'default property alias cardData: cardsRow.data',
        'contentHeight: Math.max(height,',
        'height: Math.max(implicitHeight,',
        'Layout.fillHeight: true',
        'Layout.preferredWidth: 1',
        'objectName: "cloudFileDetailsOverviewFileCard"',
        'objectName: "cloudFileDetailsOverviewCompatibilityCard"',
        'objectName: "cloudFileDetailsTechnicalTab"',
        'visible: root.showAdvancedDetails',
        'objectName: "cloudFileDetailsCloudMetadataTab"',
        'text: qsTr("Cloud Metadata")',
        'visible: root.buildDebugEnabled',
        'objectName: "cloudFileDetailsCloudMetadataPanel"',
        'objectName: "cloudFileDetailsPrintButton"',
    ):
        if required not in details_text:
            issues.append(f"CloudFileDetailsDialog missing `{required}`")


    if details_text.count("DetailsPanel {") != 4:
        issues.append("CloudFileDetailsDialog must define one DetailsPanel component and use it for four tabs")

    details_card_start = details_text.find("component DetailsCard: Rectangle {")
    details_panel_start = details_text.find("component DetailsPanel: Flickable {")
    details_card_text = (
        details_text[details_card_start:details_panel_start]
        if 0 <= details_card_start < details_panel_start
        else ""
    )
    for required in (
        "default property alias contentData: detailsBody.data",
        "id: detailsBody",
        'objectName: "cloudFileDetailsCardBody"',
        "Layout.fillHeight: false",
        "Layout.maximumHeight: implicitHeight",
        "Layout.alignment: Qt.AlignTop",
        "Item {\n                Layout.fillWidth: true\n                Layout.fillHeight: true",
    ):
        if required not in details_card_text:
            issues.append(
                "CloudFileDetailsDialog DetailsCard must keep its field body compact at the top "
                f"and absorb remaining height below it with `{required}`"
            )

    for compact_row_token in (
        "Layout.fillHeight: false",
        "Layout.minimumHeight: implicitHeight",
        "Layout.preferredHeight: implicitHeight",
        "Layout.maximumHeight: implicitHeight",
        "Layout.alignment: Qt.AlignTop",
    ):
        if details_text.count(compact_row_token) < 2:
            issues.append(
                "CloudFileDetailsDialog DetailRow and SummaryField must both enforce "
                f"compact natural-height rows with `{compact_row_token}`"
            )

    footer_marker = "footerTrailingData: ["
    footer_index = details_text.find(footer_marker)
    if footer_index < 0:
        issues.append("CloudFileDetailsDialog missing footerTrailingData")
    else:
        footer_text = details_text[footer_index:]
        close_index = footer_text.find('objectName: "cloudFileDetailsCloseButton"')
        download_index = footer_text.find('objectName: "cloudFileDetailsDownloadButton"')
        print_index = footer_text.find('objectName: "cloudFileDetailsPrintButton"')
        if not (0 <= close_index < download_index < print_index):
            issues.append("CloudFileDetailsDialog footer actions must be ordered Close, Download, Print")
        if footer_text.count("Layout.minimumWidth: 112") < 3:
            issues.append("CloudFileDetailsDialog footer actions must use a consistent minimum width")

    for forbidden in (
        'fileData.downloadUrl',
        'qsTr("Download URL")',
        'qsTr("Thumbnail URL")',
        'ID: %1 | status_code:',
    ):
        if forbidden in details_text:
            issues.append(f"CloudFileDetailsDialog exposes forbidden standard detail `{forbidden}`")

    page_text = read_text(cloud_files_page)
    if 'showAdvancedDetails: root.showAdvancedDetails' not in page_text:
        issues.append("CloudFilesPage does not forward the advanced-details setting")

    main_text = read_text(main_window)
    for required in (
        'ui.cloudFiles.showAdvancedDetails',
        'objectName: "settingsTechnicalDetailsCheckBox"',
        'showAdvancedDetails: root.cloudFileAdvancedDetailsEnabled',
    ):
        if required not in main_text:
            issues.append(f"MainWindow cloud-file settings contract missing `{required}`")

    checkbox_marker = 'objectName: "settingsTechnicalDetailsCheckBox"'
    marker_index = main_text.find(checkbox_marker)
    if marker_index >= 0:
        next_section = main_text.find('SectionHeader {', marker_index + len(checkbox_marker))
        checkbox_block = main_text[marker_index:next_section if next_section >= 0 else len(main_text)]
        for required in (
            'checked: root.cloudFileAdvancedDetailsEnabled',
            'onToggled: root.persistCloudFileDetailsSetting(checked)',
        ):
            if required not in checkbox_block:
                issues.append(
                    f"MainWindow advanced-details checkbox contract missing `{required}`"
                )

    return issues


def find_legacy_alias_usage() -> list[str]:
    legacy = ("textPrimary", "textSecondary", "panel", "card", "panelStroke", "cardAlt")
    files_to_check = [
        QML_ROOT / "MainWindow.qml",
        QML_ROOT / "dialogs" / "PrintDraftDialog.qml",
        QML_ROOT / "dialogs" / "UploadDraftDialog.qml",
        QML_ROOT / "dialogs" / "SessionSettingsDialog.qml",
        QML_ROOT / "pages" / "CloudFilesPage.qml",
        QML_ROOT / "pages" / "CloudFileDetailsDialog.qml",
        QML_ROOT / "pages" / "PrinterPage.qml",
        QML_ROOT / "components" / "BusyOverlay.qml",
        QML_ROOT / "components" / "ErrorBanner.qml",
        QML_ROOT / "components" / "ProgressCard.qml",
        QML_ROOT / "components" / "FileCard.qml",
    ]

    offenders: list[str] = []
    for path in files_to_check:
        text = read_text(path)
        for alias in legacy:
            if re.search(rf"\bTheme\.{re.escape(alias)}\b", text):
                offenders.append(f"{path.relative_to(REPO_ROOT)} uses Theme.{alias}")
    return offenders


def check_runtime_status_rules() -> list[str]:
    issues: list[str] = []
    status_files = [
        QML_ROOT / "MainWindow.qml",
        QML_ROOT / "pages" / "CloudFilesPage.qml",
        QML_ROOT / "pages" / "PrinterPage.qml",
        QML_ROOT / "dialogs" / "SessionSettingsDialog.qml",
    ]
    status_targets = r"(statusMsg|statusMessage|statusText|globalStatusMsg)"

    # Rule A: no status text built by free string concatenation.
    concat_re = re.compile(rf"\b{status_targets}\b\s*=\s*[^\n;]*\+")
    # Rule B: no raw backend text assigned directly to user-visible statuses.
    raw_re = re.compile(rf"\b{status_targets}\b\s*=\s*String\(")

    for path in status_files:
        text = read_text(path)
        for match in concat_re.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            issues.append(
                f"{path.relative_to(REPO_ROOT)}:{line} status assignment uses concatenation"
            )
        for match in raw_re.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            issues.append(
                f"{path.relative_to(REPO_ROOT)}:{line} status assignment uses raw String(...)"
            )

    return issues


def _extract_function_block(text: str, fn_name: str) -> str:
    fn_match = re.search(rf"\b{re.escape(fn_name)}\s*\([^)]*\)\s*\{{", text)
    if not fn_match:
        return ""
    start = fn_match.end() - 1
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return ""


def check_backend_message_contract() -> list[str]:
    issues: list[str] = []
    finalize_owners = [
        APP_ROOT / "cloud" / "CloudBridgeSupport.cpp",
        APP_ROOT / "SessionImportBridge.cpp",
    ]
    required_tokens = (
        'out.insert("messageKey"',
        'out.insert("fallbackMessage"',
        'out.insert("params"',
    )

    for path in finalize_owners:
        text = read_text(path)
        block = _extract_function_block(text, "finalizeUiMessage")
        if not block:
            issues.append(f"{path.relative_to(REPO_ROOT)} missing finalizeUiMessage()")
            continue
        for token in required_tokens:
            if token not in block:
                issues.append(
                    f"{path.relative_to(REPO_ROOT)} finalizeUiMessage() missing `{token}`"
                )

    explicit_message_sources = [
        APP_ROOT / "CloudBridge.cpp",
        APP_ROOT / "cloud" / "CloudUploadController.cpp",
        APP_ROOT / "SessionImportBridge.cpp",
    ]
    explicit_count = sum(
        read_text(path).count('out.insert("messageKey"')
        for path in explicit_message_sources
    )
    if explicit_count < 10:
        issues.append("backend adapters have too few explicit messageKey assignments")

    return issues



def check_print_workflow_boundaries() -> list[str]:
    issues: list[str] = []
    printer_page = QML_ROOT / "pages" / "PrinterPage.qml"
    printer_text = read_text(printer_page)
    cloud_header = APP_ROOT / "CloudBridge.h"
    cloud_text = read_text(cloud_header)

    required_qml = (
        "printWorkflowBridge.trackDirectPrint(operation)",
        "printWorkflowBridge.reconcileDirectPrints(list)",
        "printWorkflowBridge.trackRemotePrintCleanup",
        "printWorkflowBridge.beginRemotePostPrintCleanup",
        "printWorkflowBridge.beginRemotePrintPreparation",
        "printWorkflowBridge.evaluateRemotePrintGuard",
        "cloudBridge.evaluateLocalPrinterFileCompatibility",
    )
    for token in required_qml:
        if token not in printer_text:
            issues.append(f"PrinterPage print workflow boundary missing `{token}`")

    forbidden_qml = (
        "cloudBridge.savePendingDirectPrint",
        "cloudBridge.removePendingDirectPrint",
        "cloudBridge.loadPendingDirectPrints",
        "pendingDirectLocalDeleteByMsgId",
        "pendingDirectLocalDeleteInFlightByPrinterId",
        "onPrinterFileActionReceived",
        "handleDirectLocalDeleteConfirmation",
        "direct_cleanup:",
        "post_print_local_delete:",
        "local_file_delete:",
        "resin_feed_start:",
        "resin_feed_stop:",
        '"kind": "postPrintLocalDelete"',
        "pendingPostPrintCloudDeleteByFileId",
        "requestPostPrintLocalDelete",
        "requestPostPrintCloudDelete",
        "maybeRunPostPrintCleanup",
        "localCompatibilityForPrinterFile",
        "fileHasLocalCompatibilityMetadata",
        "compatTokens",
        "normalizedCompatText",
        "preferredCompatiblePrinterId",
        "rebuildRemoteCompatiblePrintersModel",
        "requestRemotePrintCompatibilityAsync",
        "handleCompatiblePrintersByFileIdReady",
        "handleCompatiblePrintersByExtReady",
        "cloudBridge.fetchCompatiblePrintersByFileIdAsync",
        "cloudBridge.fetchCompatiblePrintersByExtAsync",
        "pendingDirectPrintByPrinterId",
        "pendingDirectCloudDeleteByFileId",
        "restorePendingDirectPrints",
        "matchingProjectForDirectOperation",
        "requestDirectLocalDelete",
        "requestDirectCloudDelete",
        "finalizeFailedDirectPrint",
        "reconcilePendingDirectPrints",
        "beginDirectLocalDelete",
        "handleDirectLocalDeleteDispatch",
        "beginDirectCloudDelete",
        "handleDirectCloudDeleteResult",
        "directCloudDeleteRequested",
        '"kind": "directCleanup"',
    )
    for token in forbidden_qml:
        if token in printer_text:
            issues.append(f"PrinterPage still contains legacy workflow encoding `{token}`")

    forbidden_cloud_api = (
        "loadPendingDirectPrints() const",
        "savePendingDirectPrint(const QVariantMap& operation) const",
        "removePendingDirectPrint(const QString& printerId) const",
    )
    for token in forbidden_cloud_api:
        if token in cloud_text:
            issues.append(f"CloudBridge still exposes direct-print persistence `{token}`")

    if "const QVariantMap& context = QVariantMap()" not in cloud_text:
        issues.append("CloudBridge printer-order async context is not structured as QVariantMap")
    if "void printerOrderFinished(const QVariantMap& context" not in cloud_text:
        issues.append("CloudBridge printerOrderFinished signal does not expose structured context")

    workflow_header = APP_ROOT / "PrintWorkflowBridge.h"
    workflow_source = APP_ROOT / "PrintWorkflowBridge.cpp"
    store_header = APP_ROOT / "printing" / "PendingDirectPrintStore.h"
    store_source = APP_ROOT / "printing" / "PendingDirectPrintStore.cpp"
    compat_header = APP_ROOT / "printing" / "PrinterFileCompatibility.h"
    compat_source = APP_ROOT / "printing" / "PrinterFileCompatibility.cpp"
    prepare_header = APP_ROOT / "usecases" / "printing" / "PrepareRemotePrintUseCase.h"
    prepare_source = APP_ROOT / "usecases" / "printing" / "PrepareRemotePrintUseCase.cpp"
    for path in (workflow_header, workflow_source, store_header, store_source,
                 compat_header, compat_source, prepare_header, prepare_source):
        if not path.exists():
            issues.append(f"Print workflow C++ boundary missing `{path.relative_to(REPO_ROOT)}`")

    if workflow_header.exists():
        workflow_header_text = read_text(workflow_header)
        for token in (
            "void handlePrinterFileAction(",
            "Q_INVOKABLE void reconcileDirectPrints(const QVariantList& projects);",
            "void directLocalDeleteRequested(const QVariantMap& request);",
            "void directCloudDeleteRequested(const QVariantMap& operation);",
            "void directPrintTrackingReleased(const QString& printerId);",
            "void directCleanupNotice(int noticeKind);",
            "m_pendingLocalDeleteByMsgId",
            "m_directLocalDeleteInFlight",
            "trackRemotePrintCleanup",
            "beginRemotePostPrintCleanup",
            "remoteLocalDeleteRequested",
            "remoteCloudDeleteRequested",
            "beginRemotePrintPreparation",
            "remoteCompatibilityByFileIdRequested",
            "remoteCompatibilityByExtRequested",
            "remotePrintPreparationReady",
        ):
            if token not in workflow_header_text:
                issues.append(f"PrintWorkflowBridge MQTT boundary missing `{token}`")

    main_source = APP_ROOT / "main.cpp"
    main_text = read_text(main_source)
    for token in (
        "&accloud::MqttBridge::printerFileActionReceived",
        "&accloud::PrintWorkflowBridge::handlePrinterFileAction",
        "&accloud::CloudBridge::printerOrderFinished",
        "&accloud::PrintWorkflowBridge::handlePrinterOrderFinished",
        "&accloud::CloudBridge::deleteFileFinished",
        "&accloud::PrintWorkflowBridge::handleCloudDeleteFinished",
        "&accloud::PrintWorkflowBridge::directLocalDeleteRequested",
        "&accloud::PrintWorkflowBridge::directCloudDeleteRequested",
        "&accloud::CloudBridge::compatiblePrintersByFileIdReady",
        "&accloud::PrintWorkflowBridge::handleCompatiblePrintersByFileIdReady",
        "&accloud::CloudBridge::compatiblePrintersByExtReady",
        "&accloud::PrintWorkflowBridge::handleCompatiblePrintersByExtReady",
    ):
        if token not in main_text:
            issues.append(f"Desktop bootstrap MQTT workflow wiring missing `{token}`")

    return issues



def check_cloud_files_workflow_boundaries() -> list[str]:
    issues: list[str] = []
    cloud_page = QML_ROOT / "pages" / "CloudFilesPage.qml"
    cloud_text = read_text(cloud_page)

    for token in (
        "function hasCloudFilesWorkflowBridge()",
        "cloudFilesWorkflowBridge.startBatchDelete(selectedFiles)",
        "cloudFilesWorkflowBridge.deleteSingleFile(String(fileId))",
        "function onBatchDeleteStarted(total)",
        "function onBatchDeleteFinished(summary)",
        "function onSingleDeleteFinished(fileId, result)",
    ):
        if token not in cloud_text:
            issues.append(f"CloudFilesPage workflow boundary missing `{token}`")

    for token in (
        "batchDeleteQueue",
        "batchDeleteFailures",
        "batchDeleteCurrentId",
        "runNextBatchDelete",
        "handleBatchDeleteResult",
        "finishBatchDelete",
        "cloudBridge.deleteFileAsync",
        "function onDeleteFileFinished",
    ):
        if token in cloud_text:
            issues.append(f"CloudFilesPage still owns delete orchestration `{token}`")

    workflow_header = APP_ROOT / "CloudFilesWorkflowBridge.h"
    workflow_source = APP_ROOT / "CloudFilesWorkflowBridge.cpp"
    batch_header = APP_ROOT / "usecases" / "cloud" / "DeleteCloudFilesUseCase.h"
    batch_source = APP_ROOT / "usecases" / "cloud" / "DeleteCloudFilesUseCase.cpp"
    for path in (workflow_header, workflow_source, batch_header, batch_source):
        if not path.exists():
            issues.append(f"Cloud files workflow C++ boundary missing `{path.relative_to(REPO_ROOT)}`")

    if workflow_header.exists():
        header_text = read_text(workflow_header)
        for token in (
            "startBatchDelete",
            "cancelBatchDelete",
            "deleteSingleFile",
            "handleDeleteFileFinished",
            "deleteFileRequested",
            "batchDeleteFinished",
            "singleDeleteFinished",
        ):
            if token not in header_text:
                issues.append(f"CloudFilesWorkflowBridge contract missing `{token}`")

    if batch_header.exists() and "class DeleteCloudFilesUseCase" not in read_text(batch_header):
        issues.append("DeleteCloudFilesUseCase typed batch boundary is missing")

    main_text = read_text(APP_ROOT / "main.cpp")
    for token in (
        "accloud::CloudFilesWorkflowBridge cloudFilesWorkflowBridge",
        "&accloud::CloudFilesWorkflowBridge::handleDeleteFileFinished",
        "&accloud::CloudFilesWorkflowBridge::deleteFileRequested",
        'setContextProperty("cloudFilesWorkflowBridge", &cloudFilesWorkflowBridge)',
    ):
        if token not in main_text:
            issues.append(f"Desktop bootstrap cloud-files workflow wiring missing `{token}`")

    return issues


def check_qml_dead_workflow_cleanup() -> list[str]:
    issues: list[str] = []
    printer_text = read_text(QML_ROOT / "pages" / "PrinterPage.qml")
    for token in (
        "localUdiskListOrderId",
        "function uploadInputToDisplayName",
        "function progressRatio",
        "function printerSecondaryText",
        "function selectedPrinterIndex",
        "function findCloudFileInListById",
        "function buildPrinterMqttDetails",
    ):
        if token in printer_text:
            issues.append(f"PrinterPage retains dead workflow/UI helper `{token}`")

    cloud_text = read_text(QML_ROOT / "pages" / "CloudFilesPage.qml")
    for token in (
        "pwszCloudUpdateResultVisible",
        "function fileMatchesFilter",
        "function displayStatus",
        "function statusColor",
        "function isFileSelected",
    ):
        if token in cloud_text:
            issues.append(f"CloudFilesPage retains dead helper `{token}`")
    return issues


def check_residual_ui_debt() -> list[str]:
    issues: list[str] = []

    cloud_paths = (
        QML_ROOT / "pages" / "CloudFilesPage.qml",
        QML_ROOT / "pages" / "CloudFileDetailsDialog.qml",
        QML_ROOT / "pages" / "CloudFilesTablePanel.qml",
        QML_ROOT / "pages" / "CloudFilesTableRow.qml",
    )
    for path in cloud_paths:
        text = read_text(path)
        for token in ("renameRequested", "requestRename", "Rename not implemented yet"):
            if token in text:
                issues.append(
                    f"unsupported cloud rename surface remains in {path.relative_to(REPO_ROOT)}: `{token}`"
                )

    dialog_frame = read_text(QML_ROOT / "components" / "AppDialogFrame.qml")
    for token in (
        'readonly property Item overlayItem:',
        'parent: root.overlayItem',
        'anchors.centerIn: root.overlayItem',
    ):
        if token not in dialog_frame:
            issues.append(f"AppDialogFrame overlay safety contract missing `{token}`")
    if 'parent: Overlay.overlay' in dialog_frame:
        issues.append("AppDialogFrame assigns Overlay.overlay directly to QObject parent")

    upload_dialog = read_text(QML_ROOT / "components" / "UploadFileDialog.qml")
    if 'parent: Overlay.overlay' in upload_dialog:
        issues.append("UploadFileDialog bypasses the normalized overlay parent")

    main_window = read_text(QML_ROOT / "MainWindow.qml")
    guarded_status = 'root !== null && root !== undefined'
    if main_window.count(guarded_status) < 2:
        issues.append("MainWindow status forwarding is not guarded during object teardown")

    return issues

def check_incremental_printer_models() -> list[str]:
    issues: list[str] = []
    printer_page = QML_ROOT / "pages" / "PrinterPage.qml"
    text = read_text(printer_page)

    forbidden = (
        "remoteCompatiblePrintersModel",
        "printCloudFilesModel",
        "printerLocalFilesModel",
    )
    for object_id in forbidden:
        pattern = rf"ListModel\s*\{{(?:(?!\}}).)*?id:\s*{re.escape(object_id)}\b"
        if re.search(pattern, text, flags=re.DOTALL):
            issues.append(
                f"PrinterPage still rebuilds `{object_id}` as a QML ListModel"
            )

    required = (
        "PrinterFilesModel {",
        "remoteCompatiblePrintersModel.replaceOrPatchPrinters(preparation.compatiblePrinters || [])",
        "printCloudFilesModel.replaceOrPatchFiles(compatibleFiles)",
        "printerLocalFilesModel.replaceOrPatchFiles(localFiles)",
    )
    for token in required:
        if token not in text:
            issues.append(f"PrinterPage incremental model contract missing `{token}`")

    model_header = APP_ROOT / "PrinterFilesModel.h"
    model_source = APP_ROOT / "PrinterFilesModel.cpp"
    if not model_header.exists() or not model_source.exists():
        issues.append("PrinterFilesModel C++ implementation is missing")

    return issues

def check_v1_printer_controls() -> list[str]:
    issues: list[str] = []
    detail = read_text(QML_ROOT / "pages" / "PrinterDetailPanel.qml")
    remote = read_text(QML_ROOT / "pages" / "PrinterRemotePrintConfigDialog.qml")
    page = read_text(QML_ROOT / "pages" / "PrinterPage.qml")

    for suffix in ("Basic", ""):
        for number in ("1", "2", "3"):
            token = f'objectName: "printerFunctionB{number}Button{suffix}"'
            if token in detail:
                issues.append(f"PrinterDetailPanel retains nonfunctional {token}")
        feeding = f'objectName: "printerFunctionFeedingButton{suffix}"'
        if feeding not in detail:
            issues.append(f"PrinterDetailPanel missing functional {feeding}")

    if "root.resinFeedRequested(printerId, 1)" not in detail or "root.resinFeedRequested(printerId, 2)" not in detail:
        issues.append("PrinterDetailPanel resin feeding workflow is no longer wired")
    if "root.startResinFeedOperation(printerId, feedType)" not in page:
        issues.append("PrinterPage resin feeding operation is no longer wired")

    for token in ("Lift compensation", "Auto resin check", "optionLiftCompensation", "optionAutoResinCheck"):
        if token in remote or token in page:
            issues.append(f"Unwired remote print option remains: {token}")
    for token in ('objectName: "remotePrintOptionsCard"', 'visible: root.directPrintMode',
                  'objectName: "directPrintDeleteAfterSuccess"'):
        if token not in remote:
            issues.append(f"Remote print cleanup option contract missing: {token}")
    return issues


def check_printer_phase_layout() -> list[str]:
    """Keep preparation transient and the compact printer header single-row."""
    issues: list[str] = []
    details = read_text(QML_ROOT / "pages" / "PrinterDetailPanel.qml")
    panel = read_text(QML_ROOT / "pages" / "PrinterMainPanel.qml")
    tabs = read_text(QML_ROOT / "pages" / "PrintersTabsBar.qml")
    for token in (
        'function hasStartedPrintLayers() {',
        'function printerInfoMode() {',
        'return "preparing"',
        'objectName: "printerPreparationPanel"',
        'visible: root.printerInfoMode() === "preparing"',
        'objectName: "printerActivePrintPanel"',
        'visible: root.printerInfoMode() === "printing"',
        '"value": qsTr("Waiting for the first layer")',
        'visible: !root.embeddedInTabsContainer && root.selectedPrinter !== null',
    ):
        if token not in details:
            issues.append(f"PrinterDetailPanel phase layout missing `{token}`")
    if '"value": root.layersProgressText(root.selectedPrinter)' in details:
        issues.append("Preparation steps must not duplicate the active layer counter")
    for token in (
        'objectName: "printerCompactHeader"',
        'objectName: "printerTopLocalFilesButton"',
        'objectName: "printerTopStatusChip"',
        'status: printerDetailPanel.printerDisplayStatus()',
        'visible: root.selectedPrinter !== null && !root.activePrintVisible',
        'fleetRevision: root.fleetRevision',
        'border.width: 0',
        'objectName: "printerHeaderRightBaseline"',
        'objectName: "printerPanelLeftOutline"',
        'objectName: "printerPanelRightOutline"',
        'objectName: "printerPanelBottomOutline"',
        'onClicked: {',
        'root.localFileRequested(root.selectedPrinterId)',
    ):
        if token not in panel:
            issues.append(f"PrinterMainPanel compact header missing `{token}`")
    for required in (
        "activePrintFileParameters(",
        "merged.mqttPrintParameters = mqttParams",
    ):
        if required not in read_text(QML_ROOT / "pages" / "PrinterPage.qml"):
            issues.append(f"PrinterPage MQTT file settings bridge missing `{required}`")
    for required in (
        "function mqttPrintMetadataText(name)",
        "var mqttValue = mqttPrintMetadataText(name)",
    ):
        if required not in details:
            issues.append(f"PrinterDetailPanel MQTT metadata projection missing `{required}`")
    if "test_printer_active_file_mqtt_metadata_precedence_and_reset" not in read_text(REPO_ROOT / "tests/ui/qml/tst_control_room.qml"):
        issues.append("Missing QML regression for MQTT file metadata and stale-state reset")
    for token in ('TextMetrics {',
                  'Math.ceil(printerTabTitleMetrics.advanceWidth)',
                  'clip: true'):
        if token not in tabs:
            issues.append(f"Printer tabs must size/clip full labels with `{token}`")
    tab_button = read_text(QML_ROOT / "components" / "AppTabButton.qml")
    for token in ('readonly property int verticalBorderBottomMargin: (checked && connectActiveToPanel',
                  'z: 1', 'onConnectActiveToPanelChanged: tabStrokeCanvas.requestPaint()'):
        if token not in tab_button:
            issues.append(f"Active tab side stroke must attach to panel: `{token}`")
    for token in (
        'objectName: "printerActiveFileMetadataCard"',
        'visible: root.printerInfoMode() === "printing"',
        'function fileMetadataValue(name)',
        'function fileMetadataRows(column)',
        'qsTr("Estimated resin")',
        'qsTr("Estimated duration")',
        'qsTr("Normal exposure time")',
        'qsTr("Bottom exposure time")',
        'qsTr("Off time")',
        'return qsTr("N/A")',
    ):
        if token not in details:
            issues.append(f"Printer file parameters missing `{token}`")
    for token in (
        'function activeFileMetadataIdentity()',
        'function matchingActiveCloudFile(files)',
        'function acceptActiveCloudFileMetadata(files)',
        'cloudBridge.loadCachedFilesAsync(1, 200)',
        'selectedFileMetadata: root.activeCloudFileMetadata',
    ):
        if token not in read_text(QML_ROOT / "pages" / "PrinterPage.qml"):
            issues.append(f"Printer cache-only file metadata lookup missing `{token}`")
    for name in (
        'test_printer_active_file_parameters_display_and_phase_reset',
        'test_printer_active_file_cache_matching_never_uses_filename',
    ):
        if name not in read_text(REPO_ROOT / "tests/ui/qml/tst_control_room.qml"):
            issues.append(f"Missing printer file parameters regression `{name}`")
    if 'visible: root.printerInfoMode() === "preparing"' not in details:
        issues.append("Printer Functions card must disappear during real print tracking")
    if 'root.fleetRevision' not in tabs or 'root.selectedPrinterSnapshot' not in tabs:
        issues.append("Printer tab labels must refresh on fleet and selected telemetry changes")
    page = read_text(QML_ROOT / "pages" / "PrinterPage.qml")
    for token in ('function printerTabTitle(printer) {',
                  'selectedPrinterLiveSnapshot', 'qsTr("%1 %")',
                  'qsTr("Preparing")', 'qsTr("Offline")'):
        if token not in page:
            issues.append(f"Printer fleet tab status missing `{token}`")
    tests = read_text(REPO_ROOT / "tests" / "ui" / "qml" / "tst_control_room.qml")
    for name in (
        'test_printer_preparation_switches_to_print_tracking_only_on_real_progress',
        'test_printer_compact_header_contains_selected_name_controls_and_status',
        'test_printer_tabs_report_each_printer_state_and_print_percent_only',
        'test_printer_tab_full_title_and_attached_side_strokes',
        'test_printer_functions_card_visibility_and_feeding_modal_ui',
    ):
        if name not in tests:
            issues.append(f"Missing QML regression `{name}`")
    return issues


def main() -> int:
    errors: list[str] = []

    raw_dialogs = find_raw_dialogs()
    if raw_dialogs:
        errors.append("Raw Dialog usage found outside AppDialogFrame:")
        errors.extend(f"- {p.relative_to(REPO_ROOT)}" for p in raw_dialogs)

    errors.extend(f"- {msg}" for msg in check_tabs_config())
    errors.extend(f"- {msg}" for msg in check_tabs_geometry_v2())
    errors.extend(f"- {msg}" for msg in check_tab_stroke_tokens())
    errors.extend(f"- {msg}" for msg in check_reactive_theme_contract())
    errors.extend(f"- {msg}" for msg in check_form_components())
    errors.extend(f"- {msg}" for msg in check_runtime_status_rules())
    errors.extend(f"- {msg}" for msg in check_backend_message_contract())
    errors.extend(f"- {msg}" for msg in check_incremental_printer_models())
    errors.extend(f"- {msg}" for msg in check_print_workflow_boundaries())
    errors.extend(f"- {msg}" for msg in check_cloud_files_workflow_boundaries())
    errors.extend(f"- {msg}" for msg in check_qml_dead_workflow_cleanup())
    errors.extend(f"- {msg}" for msg in check_residual_ui_debt())
    errors.extend(f"- {msg}" for msg in check_cloud_file_details_contract())
    errors.extend(f"- {msg}" for msg in check_v1_printer_controls())
    errors.extend(f"- {msg}" for msg in check_printer_phase_layout())

    legacy_usage = find_legacy_alias_usage()
    if legacy_usage:
        errors.append("Legacy theme aliases found in migrated files:")
        errors.extend(f"- {msg}" for msg in legacy_usage)

    if errors:
        print("UI migration check: FAILED")
        print("\n".join(errors))
        return 1

    print("UI migration check: OK")
    print("- No raw Dialog outside AppDialogFrame")
    print("- Tabs configuration conforms to T1/T2/T3")
    print("- Tabs geometry/structure conforms to v2 corrections")
    print("- Tab stroke tokens standardized in Theme.js")
    print("- Form components conform to T3 corrections")
    print("- Runtime statuses avoid raw text and free concatenation")
    print("- Backend UI message envelope contract is enforced")
    print("- Printer selection lists use incremental C++ models")
    print("- Direct print persistence, reconciliation and cleanup use the C++ workflow boundary")
    print("- Cloud file deletion sequencing uses the C++ workflow boundary")
    print("- Unsupported rename/viewer surfaces and teardown warnings are guarded")
    print("- Cloud file details keep standard and technical data separated")
    print("- Printer preparation/printing phases and compact header protected")
    print("- No legacy theme aliases in migrated files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
