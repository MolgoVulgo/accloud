import QtQuick 2.15
import QtQuick.Layouts 1.15

import "../components"

Rectangle {
    id: root
    objectName: "printersTabsBar"

    property var printersModel: null
    property string selectedPrinterId: ""
    property var tabTitleProvider: null
    property int fleetRevision: 0
    property var selectedPrinterSnapshot: null
    property bool embeddedInTabsContainer: false

    signal printerSelected(string printerId)

    Layout.fillWidth: true
    Layout.preferredHeight: 42
    radius: embeddedInTabsContainer ? 0 : Theme.radiusControl
    color: Theme.bgSurface
    border.width: embeddedInTabsContainer ? 0 : Theme.borderWidth
    border.color: Theme.borderDefault

    AppTabBar {
        id: printersTabBar
        anchors.fill: parent
        tabVariant: "local"
        tabLook: "classic"
        tabSizingMode: "content"
        minTabWidth: 180
        connectActiveToPanel: true
        panelColor: Theme.bgSurface
        stripColor: Theme.bgSurface
        tabTopCornerRadius: embeddedInTabsContainer ? Theme.radiusControl : root.radius
        // TabBar remains flickable when multiple complete titles overflow.
        // Clip the viewport so a long label never paints over right-side actions.
        clip: true

        Repeater {
            model: root.printersModel

            AppTabButton {
                id: printerTabButton
                objectName: "printerTabButton"
                required property int index
                readonly property var printer: root.printersModel.get(index)
                // The QML Text contentItem can keep a stale/elided implicitWidth
                // when the state suffix changes. Measure the untruncated title.
                TextMetrics {
                    id: printerTabTitleMetrics
                    font: printerTabButton.font
                    text: printerTabButton.text
                }
                width: Math.max(minimumTabWidth,
                                Math.ceil(printerTabTitleMetrics.advanceWidth)
                                + leftPadding + rightPadding + 12)
                text: {
                    root.fleetRevision
                    root.selectedPrinterSnapshot
                    // Fetch after reading the revision: C++ get(index) returns a map
                    // whose individual JS fields do not notify QML bindings.
                    var current = root.printersModel && typeof root.printersModel.get === "function"
                            ? root.printersModel.get(index) : printer
                    return typeof root.tabTitleProvider === "function"
                            ? String(root.tabTitleProvider(current))
                            : String(current && current.name ? current.name : qsTr("Printer"))
                }
                checked: root.selectedPrinterId === String(printer && printer.id ? printer.id : "")
                onClicked: root.printerSelected(printer && printer.id ? String(printer.id) : "")
            }
        }
    }
}
