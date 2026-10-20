pragma Singleton
import QtQuick 2.15
import "Theme.js" as ThemeData

// Reactive application-wide theme shared by loaded pages, dialogs and controls.
// Keep the palette values in Theme.js; QML properties provide NOTIFY signals
// when the selected palette/accent changes, unlike JavaScript module globals.
QtObject {
    id: root
    property string themeName: "WarmLight"
    property string accentName: "Teal"
    readonly property var paletteTokens: ThemeData._paletteOrDefault(root.themeName)
    readonly property var accentTokens: ThemeData._accentOrDefault(root.accentName)

    function availableThemePresets() { return ThemeData.availableThemePresets() }
    function availableAccents() { return ThemeData.availableAccents() }
    function setThemePreset(name) {
        if (ThemeData.availableThemePresets().indexOf(name) < 0)
            return false
        root.themeName = name
        return true
    }
    function setAccent(name) {
        if (ThemeData.availableAccents().indexOf(name) < 0)
            return false
        root.accentName = name
        return true
    }
    function resetToDefaults() {
        root.themeName = "WarmLight"
        root.accentName = "Teal"
    }

    // Semantic color tokens; every binding is reevaluated on theme/accent changes.
    readonly property color bgWindow: root.paletteTokens.bgWindow
    readonly property color bgSurface: root.paletteTokens.bgSurface
    readonly property color bgDialog: root.paletteTokens.bgDialog
    readonly property color fgPrimary: root.paletteTokens.fgPrimary
    readonly property color fgSecondary: root.paletteTokens.fgSecondary
    readonly property color fgDisabled: root.paletteTokens.fgDisabled
    readonly property color borderDefault: root.paletteTokens.borderDefault
    readonly property color borderSubtle: root.paletteTokens.borderSubtle
    readonly property color borderStrong: root.paletteTokens.borderStrong
    readonly property color textMuted: root.paletteTokens.textMuted
    readonly property color danger: root.paletteTokens.danger
    readonly property color warning: root.paletteTokens.warning
    readonly property color success: root.paletteTokens.success
    readonly property color statusInfoBg: root.paletteTokens.statusInfoBg
    readonly property color statusSuccessBg: root.paletteTokens.statusSuccessBg
    readonly property color statusWarningBg: root.paletteTokens.statusWarningBg
    readonly property color statusErrorBg: root.paletteTokens.statusErrorBg
    readonly property color selectionBg: root.paletteTokens.selectionBg
    readonly property color selectionFg: root.paletteTokens.selectionFg
    readonly property color rootGradientStart: root.paletteTokens.rootGradientStart
    readonly property color rootGradientEnd: root.paletteTokens.rootGradientEnd
    readonly property color panel: root.paletteTokens.panel
    readonly property color card: root.paletteTokens.card
    readonly property color cardAlt: root.paletteTokens.cardAlt
    readonly property color mono: root.paletteTokens.mono
    readonly property color thumbStart: root.paletteTokens.thumbStart
    readonly property color thumbEnd: root.paletteTokens.thumbEnd
    readonly property color shadow: root.paletteTokens.shadow
    readonly property color overlayScrim: root.paletteTokens.overlayScrim
    readonly property color fgOnDanger: root.paletteTokens.fgOnDanger
    readonly property color viewportBg: root.paletteTokens.viewportBg
    readonly property color viewportBorder: root.paletteTokens.viewportBorder
    readonly property color viewportFg: root.paletteTokens.viewportFg
    readonly property color accent: root.accentTokens.accent
    readonly property color accentFg: root.accentTokens.accentFg
    readonly property color accentStrong: root.accentTokens.accentStrong
    readonly property color accentSoft: root.accentTokens.accentSoft
    readonly property color bgPanel: root.panel
    readonly property color bgCard: root.card
    readonly property color bgCardSubtle: root.cardAlt
    readonly property color panelStroke: root.borderDefault
    readonly property color textPrimary: root.fgPrimary
    readonly property color textSecondary: root.fgSecondary
    readonly property color accentPrimary: root.accent
    readonly property color accentSecondary: root.accentStrong
    readonly property color warn: root.warning
    readonly property color ok: root.success
    readonly property color info: root.accent
    readonly property color error: root.danger
    readonly property color stateRunning: root.accent
    readonly property color stateSuccess: root.success
    readonly property color stateWarning: root.warning
    readonly property color stateError: root.danger
    readonly property color tabStrokeColor: root.borderDefault
    readonly property color tabBaselineColor: root.borderDefault
    readonly property int fontTitlePx: ThemeData.fontTitlePx
    readonly property int fontSectionPx: ThemeData.fontSectionPx
    readonly property int fontBodyPx: ThemeData.fontBodyPx
    readonly property int fontCaptionPx: ThemeData.fontCaptionPx
    readonly property int paddingPage: ThemeData.paddingPage
    readonly property int paddingDialog: ThemeData.paddingDialog
    readonly property int gapRow: ThemeData.gapRow
    readonly property int gapSection: ThemeData.gapSection
    readonly property int controlHeight: ThemeData.controlHeight
    readonly property int radiusControl: ThemeData.radiusControl
    readonly property int radiusDialog: ThemeData.radiusDialog
    readonly property int borderWidth: ThemeData.borderWidth
    readonly property int tabStrokeWidth: root.borderWidth
    readonly property real modalScrimOpacity: root.paletteTokens.modalScrimOpacity
}
