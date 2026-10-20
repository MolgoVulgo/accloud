import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import "components"
import "pages" as Pages
import "dialogs" as Dialogs

ApplicationWindow {
    id: root
    objectName: "controlRoomWindow"
    width: 1480
    height: 920
    visible: true
    title: "accloud"
    property string statusText: qsTr("Checking active session...")
    property string globalStatusMsg: qsTr("Ready.")
    property string globalStatusSev: "info"
    property string globalStatusOpId: "op_shell_status"
    property bool buildDebugEnabled: (typeof accloudBuildDebugEnabled !== "undefined")
                                     && accloudBuildDebugEnabled === true
    property bool prodUi: (typeof accloudProdUi !== "undefined")
                          && accloudProdUi === true
    property bool viewer3dEnabled:
        (typeof accloudViewer3dEnabled === "undefined")
        || accloudViewer3dEnabled === true
    property bool debugUi: buildDebugEnabled
                               && Qt.application.arguments
                               && Qt.application.arguments.indexOf("--debug-ui") !== -1
    property string sessionTargetPath: ""
    property string persistedThemeName: "WarmLight"
    property string persistedAccentName: "Teal"
    property string persistedLanguageCode: "system"
    property bool pwszPreviewCompletionEnabled: true
    property bool pwszPreviewConfirmationEnabled: true
    property bool cloudFileAdvancedDetailsEnabled: false
    property bool directDeleteLocalOnFailureEnabled: false
    property int render3dWorkerCount: 6
    // Zero denotes a legacy absolute worker setting, not a selected CPU ratio.
    property int render3dWorkerRatio: 0
    property int availableLogicalCores: {
        var count = (typeof accloudAvailableLogicalCores !== "undefined")
                    ? Number(accloudAvailableLogicalCores) : 8
        return isFinite(count) && count >= 1 ? Math.floor(count) : 8
    }
    property string render3dPalettePreset: "technical_cyan"
    readonly property color render3dPartColor: root.render3dPaletteFor(root.render3dPalettePreset).partColor
    readonly property color render3dBackgroundColor: root.render3dPaletteFor(root.render3dPalettePreset).backgroundColor
    readonly property string directDeleteLocalOnFailureSettingsKey: "printing.directDeleteLocalOnFailure"
    readonly property string cloudFileAdvancedDetailsSettingsKey: "ui.cloudFiles.showAdvancedDetails"
    readonly property string render3dWorkerCountSettingsKey: "render3d.workerCount"
    readonly property string render3dWorkerRatioSettingsKey: "render3d.workerRatio"
    readonly property string render3dPalettePresetSettingsKey: "render3d.palettePreset"

    function hasUiSettingsBridge() {
        return (typeof uiSettingsBridge !== "undefined")
                && uiSettingsBridge !== null
                && typeof uiSettingsBridge.getString === "function"
                && typeof uiSettingsBridge.setString === "function"
    }

    function hasI18nBridge() {
        return (typeof appI18nBridge !== "undefined")
                && appI18nBridge !== null
                && typeof appI18nBridge.setLanguage === "function"
                && appI18nBridge.languageCode !== undefined
                && appI18nBridge.effectiveLanguageCode !== undefined
    }

    function translateLocalizedText(rawText) {
        var text = String(rawText || "")
        if (text.length === 0)
            return text

        var replacements = {
            "请求被接受": qsTr("Request accepted"),
            "操作成功": qsTr("Operation successful"),
            "连接成功": qsTr("Connection successful"),
            "用户不存在": qsTr("User does not exist"),
            "设备离线": qsTr("Printer offline"),
            "打印中": qsTr("Printing in progress"),
            "失败": qsTr("Failed"),
            "成功": qsTr("Success"),
            "错误": qsTr("Error"),
            "超时": qsTr("Timeout")
        }

        for (var key in replacements) {
            if (Object.prototype.hasOwnProperty.call(replacements, key))
                text = text.split(key).join(replacements[key])
        }

        if (/[\u4e00-\u9fff]/.test(text))
            text = text.replace(/[\u4e00-\u9fff]+/g, qsTr("localized backend message"))

        return text
    }

    function backendStatusText(rawMessage, fallbackMessage) {
        var text = translateLocalizedText(String(rawMessage || "").trim())
        return text.length > 0 ? text : String(fallbackMessage || qsTr("Operation status unavailable."))
    }

    function pushGlobalStatus(message, severity, operationId) {
        var msg = String(message || "").trim()
        if (msg.length === 0)
            return
        globalStatusMsg = translateLocalizedText(msg)
        globalStatusSev = String(severity || "info")
        globalStatusOpId = String(operationId || "op_shell_status")
    }

    function applyThemeSelection(themeNameValue, accentNameValue, persist) {
        var candidateTheme = String(themeNameValue || "").trim()
        if (candidateTheme.length === 0 || !Theme.setThemePreset(candidateTheme)) {
            candidateTheme = "WarmLight"
            Theme.setThemePreset(candidateTheme)
        }

        var candidateAccent = String(accentNameValue || "").trim()
        if (candidateAccent.length === 0 || !Theme.setAccent(candidateAccent)) {
            candidateAccent = "Teal"
            Theme.setAccent(candidateAccent)
        }

        if (persist === true) {
            root.persistedThemeName = Theme.themeName
            root.persistedAccentName = Theme.accentName
            if (root.hasUiSettingsBridge()) {
                uiSettingsBridge.setString("ui.themeName", root.persistedThemeName)
                uiSettingsBridge.setString("ui.accentName", root.persistedAccentName)
                if (typeof uiSettingsBridge.sync === "function")
                    uiSettingsBridge.sync()
            }
        }

    }

    function restorePersistedTheme() {
        root.applyThemeSelection(root.persistedThemeName, root.persistedAccentName, false)
    }

    function loadThemeFromSettings() {
        var themeValue = "WarmLight"
        var accentValue = "Teal"

        if (root.hasUiSettingsBridge()) {
            themeValue = uiSettingsBridge.getString("ui.themeName", themeValue)
            accentValue = uiSettingsBridge.getString("ui.accentName", accentValue)
        }

        root.applyThemeSelection(themeValue, accentValue, false)
        root.persistedThemeName = Theme.themeName
        root.persistedAccentName = Theme.accentName

        if (root.hasUiSettingsBridge()) {
            // Normalize persisted values if they were invalid.
            uiSettingsBridge.setString("ui.themeName", root.persistedThemeName)
            uiSettingsBridge.setString("ui.accentName", root.persistedAccentName)
            if (typeof uiSettingsBridge.sync === "function")
                uiSettingsBridge.sync()
        }
    }

    function loadLanguageFromSettings() {
        if (!root.hasI18nBridge())
            return
        root.persistedLanguageCode = String(appI18nBridge.languageCode || "system")
    }

    function maximumRender3dWorkers() {
        return Math.max(1, root.availableLogicalCores - 2)
    }

    function minimumRender3dWorkers() {
        return root.availableLogicalCores >= 8 ? 6 : 1
    }

    function normalizeRender3dWorkerCount(value) {
        var parsed = Number(value)
        if (!isFinite(parsed))
            parsed = 6
        return Math.max(root.minimumRender3dWorkers(),
                        Math.min(root.maximumRender3dWorkers(), Math.round(parsed)))
    }

    function normalizeRender3dWorkerRatio(value) {
        var parsed = Number(value)
        return isFinite(parsed) && Math.floor(parsed) === parsed
                && parsed >= 1 && parsed <= 4 ? parsed : 0
    }

    function workerCountForRatio(ratio) {
        var normalized = root.normalizeRender3dWorkerRatio(ratio)
        if (normalized === 0)
            return root.normalizeRender3dWorkerCount(root.render3dWorkerCount)
        return root.normalizeRender3dWorkerCount(
                    Math.ceil(root.maximumRender3dWorkers() * normalized / 4))
    }

    function workerRatioForCount(count) {
        var best = 1
        var bestDistance = Math.abs(root.workerCountForRatio(1) - count)
        for (var ratio = 2; ratio <= 4; ++ratio) {
            var distance = Math.abs(root.workerCountForRatio(ratio) - count)
            if (distance <= bestDistance) {
                best = ratio
                bestDistance = distance
            }
        }
        return best
    }

    function workerRatioOptions() {
        var options = []
        // Duplicate worker counts are collapsed; the highest equivalent ratio wins.
        for (var ratio = 1; ratio <= 4; ++ratio) {
            var count = root.workerCountForRatio(ratio)
            var label = qsTr("Ratio %1/4 — %2 workers").arg(ratio).arg(count)
            if (options.length > 0 && options[options.length - 1].workers === count) {
                options[options.length - 1] = {"value": ratio, "workers": count, "label": label}
            } else {
                options.push({"value": ratio, "workers": count, "label": label})
            }
        }
        return options
    }

    function workerDisplayOptions() {
        var options = root.workerRatioOptions()
        if (root.render3dWorkerRatio === 0) {
            var saved = root.render3dWorkerCount
            var matched = false
            for (var i = 0; i < options.length; ++i) {
                if (options[i].workers === saved) {
                    matched = true
                    break
                }
            }
            if (!matched)
                options.unshift({"value": 0, "workers": saved,
                                 "label": qsTr("Saved custom setting — %1 workers").arg(saved)})
        }
        return options
    }

    function workerOptionIndexForRatio(ratio) {
        var options = root.workerDisplayOptions()
        if (ratio === 0) {
            for (var oldIndex = 0; oldIndex < options.length; ++oldIndex) {
                if (options[oldIndex].workers === root.render3dWorkerCount)
                    return oldIndex
            }
        }
        var count = root.workerCountForRatio(ratio)
        for (var index = 0; index < options.length; ++index) {
            if (options[index].workers === count)
                return index
        }
        return 0
    }

    function languageOptions() {
        return [
            {"value": "system", "label": qsTr("System default")},
            {"value": "en", "label": qsTr("English")},
            {"value": "fr", "label": qsTr("French")}
        ]
    }

    function languageOptionIndex(code) {
        var options = root.languageOptions()
        for (var i = 0; i < options.length; ++i) {
            if (options[i].value === code)
                return i
        }
        return 0
    }

    function render3dPaletteOptions() {
        return [
            {
                "id": "technical_cyan",
                "label": qsTr("Technical cyan"),
                "partColor": "#55B7C6",
                "backgroundColor": "#171A1F"
            },
            {
                "id": "industrial_amber",
                "label": qsTr("Industrial amber"),
                "partColor": "#F2B84B",
                "backgroundColor": "#20242B"
            },
            {
                "id": "mineral_ivory",
                "label": qsTr("Mineral ivory"),
                "partColor": "#E8E2D6",
                "backgroundColor": "#243447"
            },
            {
                "id": "night_coral",
                "label": qsTr("Night coral"),
                "partColor": "#FF7A66",
                "backgroundColor": "#111827"
            },
            {
                "id": "light_graphite",
                "label": qsTr("Light graphite"),
                "partColor": "#334155",
                "backgroundColor": "#F4F1EA"
            }
        ]
    }

    function normalizeRender3dPalettePreset(value) {
        var requested = String(value || "").trim()
        var options = root.render3dPaletteOptions()
        for (var i = 0; i < options.length; ++i) {
            if (String(options[i].id) === requested)
                return requested
        }
        return "technical_cyan"
    }

    function render3dPaletteFor(value) {
        var normalized = root.normalizeRender3dPalettePreset(value)
        var options = root.render3dPaletteOptions()
        for (var i = 0; i < options.length; ++i) {
            if (String(options[i].id) === normalized)
                return options[i]
        }
        return options[0]
    }

    function render3dPaletteIndex(value) {
        var normalized = root.normalizeRender3dPalettePreset(value)
        var options = root.render3dPaletteOptions()
        for (var i = 0; i < options.length; ++i) {
            if (String(options[i].id) === normalized)
                return i
        }
        return 0
    }

    function loadRender3dSettings() {
        var configured = 6
        var ratio = 0
        var palettePreset = "technical_cyan"
        if (root.hasUiSettingsBridge()) {
            configured = root.normalizeRender3dWorkerCount(uiSettingsBridge.getString(
                    root.render3dWorkerCountSettingsKey, "6"))
            var savedRatio = String(uiSettingsBridge.getString(
                    root.render3dWorkerRatioSettingsKey, ""))
            ratio = savedRatio.length > 0 ? root.normalizeRender3dWorkerRatio(savedRatio) : 0
            if (ratio !== 0)
                configured = root.workerCountForRatio(ratio)
            palettePreset = root.normalizeRender3dPalettePreset(uiSettingsBridge.getString(
                    root.render3dPalettePresetSettingsKey, "technical_cyan"))
            uiSettingsBridge.setString(root.render3dWorkerCountSettingsKey, String(configured))
            uiSettingsBridge.setString(root.render3dWorkerRatioSettingsKey,
                                       ratio !== 0 ? String(ratio) : "")
            uiSettingsBridge.setString(root.render3dPalettePresetSettingsKey, palettePreset)
            if (typeof uiSettingsBridge.sync === "function")
                uiSettingsBridge.sync()
        }
        root.render3dWorkerCount = configured
        root.render3dWorkerRatio = ratio
        root.render3dPalettePreset = palettePreset
    }

    function persistRender3dWorkerCount(value) {
        root.render3dWorkerCount = root.normalizeRender3dWorkerCount(value)
        root.render3dWorkerRatio = 0
        if (!root.hasUiSettingsBridge())
            return
        uiSettingsBridge.setString(root.render3dWorkerCountSettingsKey,
                                   String(root.render3dWorkerCount))
        uiSettingsBridge.setString(root.render3dWorkerRatioSettingsKey, "")
        if (typeof uiSettingsBridge.sync === "function")
            uiSettingsBridge.sync()
    }

    function persistRender3dWorkerRatio(value) {
        var ratio = root.normalizeRender3dWorkerRatio(value)
        if (ratio === 0)
            return
        root.render3dWorkerRatio = ratio
        root.render3dWorkerCount = root.workerCountForRatio(ratio)
        if (!root.hasUiSettingsBridge())
            return
        uiSettingsBridge.setString(root.render3dWorkerRatioSettingsKey, String(ratio))
        uiSettingsBridge.setString(root.render3dWorkerCountSettingsKey,
                                   String(root.render3dWorkerCount))
        if (typeof uiSettingsBridge.sync === "function")
            uiSettingsBridge.sync()
    }

    function persistRender3dPalettePreset(value) {
        root.render3dPalettePreset = root.normalizeRender3dPalettePreset(value)
        if (!root.hasUiSettingsBridge())
            return
        uiSettingsBridge.setString(root.render3dPalettePresetSettingsKey,
                                   root.render3dPalettePreset)
        if (typeof uiSettingsBridge.sync === "function")
            uiSettingsBridge.sync()
    }

    function loadPwszUploadSettings() {
        if (!root.hasUiSettingsBridge())
            return
        root.pwszPreviewCompletionEnabled = String(uiSettingsBridge.getString(
                "cloud.upload.completePwszPreview2", "true")).toLowerCase() !== "false"
        root.pwszPreviewConfirmationEnabled = String(uiSettingsBridge.getString(
                "cloud.upload.confirmPwszPreview2", "true")).toLowerCase() !== "false"
    }

    function persistPwszUploadSetting(key, value) {
        if (!root.hasUiSettingsBridge())
            return
        uiSettingsBridge.setString(key, value === true ? "true" : "false")
        if (typeof uiSettingsBridge.sync === "function")
            uiSettingsBridge.sync()
    }

    function loadDirectPrintSettings() {
        if (!root.hasUiSettingsBridge()) {
            root.directDeleteLocalOnFailureEnabled = false
            return
        }
        root.directDeleteLocalOnFailureEnabled = String(uiSettingsBridge.getString(
                root.directDeleteLocalOnFailureSettingsKey, "false")).toLowerCase() === "true"
    }

    function persistDirectPrintFailureCleanup(value) {
        root.directDeleteLocalOnFailureEnabled = value === true
        if (!root.hasUiSettingsBridge())
            return
        uiSettingsBridge.setString(root.directDeleteLocalOnFailureSettingsKey,
                                   root.directDeleteLocalOnFailureEnabled ? "true" : "false")
        if (typeof uiSettingsBridge.sync === "function")
            uiSettingsBridge.sync()
    }

    function loadCloudFileDetailsSettings() {
        var defaultValue = root.debugUi ? "true" : "false"
        if (!root.hasUiSettingsBridge()) {
            root.cloudFileAdvancedDetailsEnabled = root.debugUi
            return
        }
        root.cloudFileAdvancedDetailsEnabled = String(uiSettingsBridge.getString(
                root.cloudFileAdvancedDetailsSettingsKey,
                defaultValue)).toLowerCase() === "true"
    }

    function persistCloudFileDetailsSetting(value) {
        root.cloudFileAdvancedDetailsEnabled = value === true
        if (!root.hasUiSettingsBridge())
            return
        uiSettingsBridge.setString(root.cloudFileAdvancedDetailsSettingsKey,
                                   root.cloudFileAdvancedDetailsEnabled ? "true" : "false")
        if (typeof uiSettingsBridge.sync === "function")
            uiSettingsBridge.sync()
    }

    function openUploadDialog() {
        uploadDialog.open()
    }

    function openPrintDialog() {
        printDialog.open()
    }

    function applyStartupCheckResult(check) {
        if (check.sessionExists === true && check.connectionOk === true) {
            root.statusText = qsTr("Active session. Auto-refresh every 30s.")
            if (typeof mqttBridge !== "undefined"
                    && mqttBridge !== null
                    && mqttBridge.connected !== true
                    && typeof mqttBridge.ensureAutoConnected === "function") {
                mqttBridge.ensureAutoConnected()
            }
        } else {
            var startupText = backendStatusText(check.message, qsTr("Session validation required."))
            root.statusText = startupText
            sessionDialog.startupMessage = startupText
            sessionDialog.mandatoryMode = true
            sessionDialog.open()
        }
    }

    Component.onCompleted: {
        root.loadThemeFromSettings()
        root.loadLanguageFromSettings()
        root.loadPwszUploadSettings()
        root.loadRender3dSettings()
        root.loadDirectPrintSettings()
        root.loadCloudFileDetailsSettings()
        Qt.callLater(function() {
            if (typeof sessionImportBridge === "undefined"
                    || sessionImportBridge === null
                    || typeof sessionImportBridge.checkStartup !== "function") {
                root.statusText = qsTr("UI mode: backend unavailable.")
                return
            }
            if (typeof sessionImportBridge.defaultSessionPath === "function") {
                root.sessionTargetPath = String(sessionImportBridge.defaultSessionPath())
            }

            if (typeof sessionImportBridge.checkStartupAsync === "function") {
                root.statusText = qsTr("Checking active session...")
                sessionImportBridge.checkStartupAsync()
                return
            }
            root.applyStartupCheckResult(sessionImportBridge.checkStartup())
        })
    }

    Connections {
        target: (typeof sessionImportBridge !== "undefined"
                 && sessionImportBridge !== null) ? sessionImportBridge : null
        ignoreUnknownSignals: true

        function onStartupCheckFinished(result) {
            root.applyStartupCheckResult(result)
        }
    }

    component HeaderActionButton: AppButton {
        variant: "secondary"
        compact: true
        font.pixelSize: Theme.fontBodyPx
    }

    background: Rectangle {
        gradient: Gradient {
            GradientStop { position: 0.0; color: Theme.rootGradientStart }
            GradientStop { position: 1.0; color: Theme.rootGradientEnd }
        }
    }

    menuBar: MenuBar {
        objectName: "mainMenuBar"

        Menu {
            objectName: "menuSession"
            title: qsTr("Session")

            MenuItem {
                objectName: "menuSessionImportHar"
                text: qsTr("Import HAR...")
                onTriggered: {
                    sessionDialog.mandatoryMode = false
                    sessionDialog.startupMessage = ""
                    sessionDialog.open()
                }
            }
        }

        Menu {
            objectName: "menuParametre"
            title: qsTr("Settings")

            MenuItem {
                objectName: "menuSettingsOpen"
                text: qsTr("Preferences...")
                onTriggered: settingsDialog.open()
            }
        }

        Menu {
            objectName: "menuHelp"
            title: qsTr("Help")

            MenuItem {
                objectName: "menuHelpAbout"
                text: qsTr("About")
                onTriggered: aboutDialog.open()
            }
        }
    }

    Dialogs.SessionSettingsDialog {
        id: sessionDialog
        objectName: "sessionSettingsDialog"
        sessionTargetPath: root.sessionTargetPath
        onImportCompleted: function(message) {
            root.statusText = qsTr("Active session. %1").arg(backendStatusText(message, qsTr("Ready.")))
            sessionDialog.mandatoryMode = false
            sessionDialog.close()
        }
        onImportSkipped: {
            root.statusText = qsTr("No active cloud session. Import a HAR from the Session menu to connect.")
            sessionDialog.mandatoryMode = false
        }
    }

    Dialogs.UploadDraftDialog {
        id: uploadDialog
        objectName: "uploadDraftDialog"
    }

    Dialogs.PrintDraftDialog {
        id: printDialog
        objectName: "printDraftDialog"
    }

    AppScrollableDialogFrame {
        id: settingsDialog
        objectName: "settingsDialog"
        title: qsTr("Settings")
        subtitle: qsTr("Choose your preferences, grouped by topic. Changes are saved immediately.")
        dialogSize: "large"
        minimumWidth: 640
        maximumWidth: 820
        maximumHeight: 800
        contentMinimumHeight: 430

        onOpened: {
            var ratio = root.render3dWorkerRatio !== 0
                    ? root.render3dWorkerRatio
                    : root.workerRatioForCount(root.render3dWorkerCount)
            settingsWorkerRatioCombo.currentIndex = root.workerOptionIndexForRatio(ratio)
            settingsThemePresetCombo.currentIndex = Math.max(0, settingsThemePresetCombo.find(root.persistedThemeName))
            settingsAccentPresetCombo.currentIndex = Math.max(0, settingsAccentPresetCombo.find(root.persistedAccentName))
            settingsLanguageCombo.currentIndex = root.languageOptionIndex(root.persistedLanguageCode)
            settingsRender3dPaletteCombo.currentIndex = root.render3dPaletteIndex(root.render3dPalettePreset)
        }

        scrollBodyData: [
            SectionHeader {
                Layout.fillWidth: true
                title: qsTr("Interface")
                subtitle: qsTr("Appearance, language and file details")
            },
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.gapRow
                Text {
                    text: qsTr("Theme")
                    color: Theme.fgPrimary
                    font.pixelSize: Theme.fontBodyPx
                    Layout.preferredWidth: 165
                }
                AppComboBox {
                    id: settingsThemePresetCombo
                    objectName: "settingsThemePresetCombo"
                    Layout.fillWidth: true
                    model: Theme.availableThemePresets()
                    onActivated: function(index) {
                        root.applyThemeSelection(String(currentText), root.persistedAccentName, true)
                    }
                }
            },
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.gapRow
                Text {
                    text: qsTr("Accent")
                    color: Theme.fgPrimary
                    font.pixelSize: Theme.fontBodyPx
                    Layout.preferredWidth: 165
                }
                AppComboBox {
                    id: settingsAccentPresetCombo
                    objectName: "settingsAccentPresetCombo"
                    Layout.fillWidth: true
                    model: Theme.availableAccents()
                    onActivated: function(index) {
                        root.applyThemeSelection(root.persistedThemeName, String(currentText), true)
                    }
                }
            },
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.gapRow
                Text {
                    text: qsTr("Language")
                    color: Theme.fgPrimary
                    font.pixelSize: Theme.fontBodyPx
                    Layout.preferredWidth: 165
                }
                AppComboBox {
                    id: settingsLanguageCombo
                    objectName: "settingsLanguageCombo"
                    Layout.fillWidth: true
                    enabled: root.hasI18nBridge()
                    model: root.languageOptions()
                    textRole: "label"
                    onActivated: function(index) {
                        if (!root.hasI18nBridge())
                            return
                        var choice = root.languageOptions()[index]
                        if (choice === undefined)
                            return
                        appI18nBridge.setLanguage(choice.value)
                        root.persistedLanguageCode = String(appI18nBridge.languageCode || "system")
                    }
                }
            },
            AppCheckBox {
                objectName: "settingsTechnicalDetailsCheckBox"
                Layout.fillWidth: true
                text: qsTr("Show technical file details")
                checked: root.cloudFileAdvancedDetailsEnabled
                onToggled: root.persistCloudFileDetailsSetting(checked)
            },
            SectionHeader {
                Layout.fillWidth: true
                title: qsTr("Printing")
                subtitle: qsTr("Direct-print cleanup")
            },
            AppCheckBox {
                objectName: "settingsDirectDeleteLocalOnFailureCheckBox"
                Layout.fillWidth: true
                text: qsTr("Delete printer-local copy when a direct print fails")
                checked: root.directDeleteLocalOnFailureEnabled
                onToggled: root.persistDirectPrintFailureCleanup(checked)
            },
            SectionHeader {
                Layout.fillWidth: true
                title: qsTr("Files / Upload")
                subtitle: qsTr("PWSZ preview preparation")
            },
            AppCheckBox {
                objectName: "settingsPwszPreviewCompletionCheckBox"
                Layout.fillWidth: true
                text: qsTr("Complete PWSZ previews before upload")
                checked: root.pwszPreviewCompletionEnabled
                onToggled: {
                    root.pwszPreviewCompletionEnabled = checked
                    root.persistPwszUploadSetting("cloud.upload.completePwszPreview2", checked)
                }
            },
            AppCheckBox {
                objectName: "settingsPwszPreviewConfirmationCheckBox"
                Layout.fillWidth: true
                text: qsTr("Confirm before modifying PWSZ files")
                checked: root.pwszPreviewConfirmationEnabled
                onToggled: {
                    root.pwszPreviewConfirmationEnabled = checked
                    root.persistPwszUploadSetting("cloud.upload.confirmPwszPreview2", checked)
                }
            },
            SectionHeader {
                Layout.fillWidth: true
                title: qsTr("3D Viewer")
                subtitle: qsTr("Mesh generation and viewport colors")
            },
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.gapRow
                enabled: root.viewer3dEnabled
                Text {
                    text: qsTr("Generation workers")
                    color: Theme.fgPrimary
                    font.pixelSize: Theme.fontBodyPx
                }
                Item { Layout.fillWidth: true }
                AppComboBox {
                    id: settingsWorkerRatioCombo
                    objectName: "settingsWorkerRatioCombo"
                    Layout.preferredWidth: 310
                    model: root.workerDisplayOptions()
                    textRole: "label"
                    onActivated: function(index) {
                        var options = root.workerDisplayOptions()
                        if (index < 0 || index >= options.length || options[index].value === 0)
                            return
                        root.persistRender3dWorkerRatio(options[index].value)
                        settingsWorkerRatioCombo.currentIndex = root.workerOptionIndexForRatio(options[index].value)
                        root.statusText = qsTr("3D generation workers updated: %1")
                                              .arg(root.render3dWorkerCount)
                    }
                }
            },
            Text {
                Layout.fillWidth: true
                visible: root.viewer3dEnabled
                text: qsTr("%1 logical cores detected. Two cores are reserved; worker counts range from %2 to %3. Changes apply to new PWSZ loads.")
                          .arg(root.availableLogicalCores)
                          .arg(root.minimumRender3dWorkers())
                          .arg(root.maximumRender3dWorkers())
                color: Theme.fgSecondary
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontCaptionPx
            },
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.gapRow
                enabled: root.viewer3dEnabled
                Text {
                    text: qsTr("3D colors")
                    color: Theme.fgPrimary
                    font.pixelSize: Theme.fontBodyPx
                    Layout.preferredWidth: 165
                }
                AppComboBox {
                    id: settingsRender3dPaletteCombo
                    objectName: "settingsRender3dPaletteCombo"
                    Layout.fillWidth: true
                    model: root.render3dPaletteOptions()
                    textRole: "label"
                    onActivated: function(index) {
                        var options = root.render3dPaletteOptions()
                        if (index >= 0 && index < options.length)
                            root.persistRender3dPalettePreset(options[index].id)
                    }
                }
            },
            Rectangle {
                objectName: "settingsRender3dPalettePreviewBackground"
                Layout.fillWidth: true
                Layout.preferredHeight: 64
                radius: Theme.radiusControl
                color: root.render3dBackgroundColor
                border.width: Theme.borderWidth
                border.color: Theme.borderDefault
                Rectangle {
                    objectName: "settingsRender3dPalettePreviewPart"
                    anchors.centerIn: parent
                    width: Math.min(parent.width * 0.42, 200)
                    height: 30
                    radius: Theme.radiusControl
                    color: root.render3dPartColor
                    border.width: 1
                    border.color: Qt.darker(color, 1.25)
                }
            }
        ]

        footerTrailingData: [
            AppButton {
                objectName: "settingsCloseButton"
                text: qsTr("Close")
                variant: "primary"
                onClicked: settingsDialog.close()
            }
        ]
    }

    AppDialogFrame {
        id: aboutDialog
        objectName: "aboutDialog"
        title: qsTr("About")
        minimumWidth: 520
        maximumWidth: 600
        maximumHeight: 460
        dialogSize: "small"

        Text {
            objectName: "aboutAppName"
            Layout.fillWidth: true
            text: "accloud"
            font.pixelSize: Theme.fontTitlePx
            font.bold: true
            color: Theme.fgPrimary
        }

        Text {
            objectName: "aboutVersionText"
            Layout.fillWidth: true
            text: qsTr("Version: %1").arg(Qt.application && Qt.application.version
                                          ? Qt.application.version : qsTr("Development build"))
            color: Theme.fgPrimary
        }

        Text {
            Layout.fillWidth: true
            text: qsTr("Independent cloud manager for compatible Anycubic resin printers.")
            wrapMode: Text.WordWrap
            color: Theme.fgPrimary
        }

        Text {
            Layout.fillWidth: true
            text: qsTr("Primary development and validation printer: Photon Mono M7 Pro.")
            wrapMode: Text.WordWrap
            color: Theme.fgSecondary
        }

        Text {
            id: aboutGithubLink
            objectName: "aboutGithubLink"
            Layout.fillWidth: true
            textFormat: Text.RichText
            text: "<a href=\"https://github.com/MolgoVulgo/anycubic-cloud-manager\">"
                  + qsTr("Source code on GitHub") + "</a>"
            color: Theme.fgPrimary
            onLinkActivated: function(link) {
                if (link === "https://github.com/MolgoVulgo/anycubic-cloud-manager")
                    Qt.openUrlExternally(link)
            }
        }

        Text {
            Layout.fillWidth: true
            text: qsTr("Independent project. Not affiliated with or endorsed by Anycubic.")
            color: Theme.fgSecondary
            wrapMode: Text.WordWrap
        }

        footerTrailingData: [
            AppButton {
                text: qsTr("Close")
                onClicked: aboutDialog.close()
            }
        ]
    }

    Loader {
        id: controlRoomShellLoader
        anchors.fill: parent
        sourceComponent: controlRoomShellComponent
    }

    Component {
        id: controlRoomShellComponent

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12

            property int currentTabIndex: controlTabs.currentIndex
            function setCurrentTabIndex(index) {
                if (index >= 0 && index < controlTabs.count) {
                    controlTabs.currentIndex = index
                }
            }

            Rectangle {
                id: controlRoomHeader
                objectName: "controlRoomHeader"
                Layout.fillWidth: true
                Layout.preferredHeight: root.debugUi ? 80 : 64
                radius: Theme.radiusDialog
                color: Theme.bgSurface
                border.width: Theme.borderWidth
                border.color: Theme.borderDefault

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Theme.paddingPage
                    anchors.rightMargin: Theme.paddingPage
                    anchors.topMargin: 8
                    anchors.bottomMargin: 8
                    spacing: Theme.gapRow

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Text {
                            id: titleLabel
                            objectName: "controlRoomTitle"
                            text: "accloud"
                            color: Theme.fgPrimary
                            font.pixelSize: 20
                            font.bold: true
                            elide: Text.ElideRight
                        }

                        Text {
                            id: subtitleLabel
                            objectName: "controlRoomSubtitle"
                            text: root.statusText
                            color: Theme.fgSecondary
                            opacity: 0.9
                            font.pixelSize: Theme.fontCaptionPx
                            elide: Text.ElideRight
                        }
                    }

                    RowLayout {
                        visible: root.debugUi
                        spacing: 8

                        HeaderActionButton {
                            id: printDialogButton
                            objectName: "printDialogButton"
                            text: qsTr("Print Dialog")
                            onClicked: root.openPrintDialog()
                        }

                        HeaderActionButton {
                            id: uploadDialogButton
                            objectName: "uploadDialogButton"
                            text: qsTr("Upload Dialog")
                            variant: "primary"
                            onClicked: root.openUploadDialog()
                        }
                    }
                }
            }

            Rectangle {
                id: tabsPanel
                objectName: "tabsPanel"
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Theme.radiusDialog
                color: "transparent"
                border.width: Theme.borderWidth
                border.color: Theme.borderDefault

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 0
                    spacing: 0

                    AppTabBar {
                        id: controlTabs
                        objectName: "controlRoomTabs"
                        Layout.fillWidth: true
                        tabVariant: "navigation"
                        tabLook: "classic"
                        tabSizingMode: "content"
                        minTabWidth: 120
                        connectActiveToPanel: true
                        panelColor: Theme.bgSurface
                        inactiveColor: "transparent"
                        stripColor: "transparent"
                        tabTopCornerRadius: Theme.radiusControl

                        AppTabButton {
                            objectName: "filesTabButton"
                            text: qsTr("Files")
                        }

                        AppTabButton {
                            objectName: "printerTabButton"
                            text: qsTr("Printers")
                        }

                        AppTabButton {
                            objectName: "mqttTabButton"
                            text: qsTr("MQTT")
                            visible: !root.prodUi
                        }

                        AppTabButton {
                            objectName: "logTabButton"
                            text: root.buildDebugEnabled
                                  ? qsTr("Logs")
                                  : qsTr("Logs (disabled in this build)")
                            visible: !root.prodUi
                        }

                        onCurrentIndexChanged: {
                            if (currentIndex === 1
                                    && printerPage
                                    && typeof printerPage.ensureStartupInitialized === "function") {
                                printerPage.ensureStartupInitialized()
                            }
                        }
                    }

                    StackLayout {
                        id: controlRoomStack
                        objectName: "controlRoomStack"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.leftMargin: Theme.borderWidth
                        Layout.rightMargin: Theme.borderWidth
                        Layout.bottomMargin: Theme.borderWidth
                        currentIndex: controlTabs.currentIndex

                        Pages.CloudFilesPage {
                            id: cloudFilesPage
                            objectName: "cloudFilesPage"
                            embeddedInTabsContainer: true
                            viewerEnabled: root.viewer3dEnabled
                            render3dWorkerCount: root.render3dWorkerCount
                            render3dPalettePreset: root.render3dPalettePreset
                            render3dPartColor: root.render3dPartColor
                            render3dBackgroundColor: root.render3dBackgroundColor
                            showAdvancedDetails: root.cloudFileAdvancedDetailsEnabled
                            onStatusBroadcast: function(message, severity, operationId) {
                                if (root !== null && root !== undefined
                                        && typeof root.pushGlobalStatus === "function") {
                                    root.pushGlobalStatus(message, severity, operationId)
                                }
                            }
                            onPwszUploadSettingsChanged: root.loadPwszUploadSettings()
                            onPrintIntentRequested: function(fileId, fileName, fileData) {
                                if (typeof printerPage.openRemotePrintFromFile === "function") {
                                    printerPage.openRemotePrintFromFile(fileId, fileName, fileData)
                                } else {
                                    root.pushGlobalStatus(qsTr("Remote print entrypoint is unavailable."),
                                                          "warn",
                                                          "op_files_print_entry")
                                }
                            }
                            onDirectPrintIntentRequested: function(localPath, fileName, completePreview) {
                                if (typeof printerPage.openDirectPrintFromLocalFile === "function") {
                                    printerPage.openDirectPrintFromLocalFile(localPath,
                                                                            fileName,
                                                                            completePreview,
                                                                            root.directDeleteLocalOnFailureEnabled)
                                } else {
                                    root.pushGlobalStatus(qsTr("Direct print entrypoint is unavailable."),
                                                          "warn",
                                                          "op_direct_print_entry")
                                }
                            }
                        }

                        Pages.PrinterPage {
                            id: printerPage
                            objectName: "printerPage"
                            embeddedInTabsContainer: true
                            developmentBuild: root.buildDebugEnabled
                            deferStartupInitialization: true
                            directDeleteLocalOnFailurePreference: root.directDeleteLocalOnFailureEnabled
                            pageActive: controlTabs.currentIndex === 1
                            onStatusBroadcast: function(message, severity, operationId) {
                                if (root !== null && root !== undefined
                                        && typeof root.pushGlobalStatus === "function") {
                                    root.pushGlobalStatus(message, severity, operationId)
                                }
                            }
                            onRemotePrintAccepted: function(printerId, taskId) {
                                controlTabs.currentIndex = 1
                            }
                        }

                        Item {
                            objectName: "mqttPageHost"
                            visible: !root.prodUi
                            Layout.fillWidth: true
                            Layout.fillHeight: true

                            Loader {
                                id: mqttPageLoader
                                anchors.fill: parent
                                active: controlTabs.currentIndex === 2
                                sourceComponent: Pages.MqttPage {
                                    objectName: "mqttPage"
                                    embeddedInTabsContainer: true
                                    pageActive: controlTabs.currentIndex === 2
                                }
                            }
                        }

                        Item {
                            objectName: "logPageHost"
                            visible: !root.prodUi
                            Layout.fillWidth: true
                            Layout.fillHeight: true

                            Loader {
                                id: logPageLoader
                                anchors.fill: parent
                                active: root.buildDebugEnabled && controlTabs.currentIndex === 3
                                source: "pages/LogPage.qml"
                            }

                            AppPageFrame {
                                anchors.fill: parent
                                visible: !root.buildDebugEnabled
                                embeddedInTabsContainer: true
                                sectionTitle: qsTr("Logs")
                                sectionSubtitle: qsTr("Debug tools are disabled in this build")

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: Theme.gapRow

                                    Text {
                                        text: qsTr("Rebuild with ACCLOUD_DEBUG=ON to enable the runtime log viewer.")
                                        color: Theme.fgSecondary
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                        }

                    }

                    InlineStatusBar {
                        objectName: "globalStatusBar"
                        Layout.fillWidth: true
                        message: root.globalStatusMsg
                        severity: root.globalStatusSev
                        operationId: root.globalStatusOpId
                        showOperationId: root.debugUi
                    }

                }
            }
        }
    }
}
