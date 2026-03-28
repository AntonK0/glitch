import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

/**
 * MUSE — AI Music Composition Assistant
 *
 * Main QML window matching the Figma design:
 *   - Dark theme panel
 *   - "MUSE" header with agent status indicator
 *   - Voice Prompt input card
 *   - Hum Melody input card
 *   - Suggest / Demo mode toggle
 *   - Last Output log panel
 */
ApplicationWindow {
    id: root
    visible: true
    width: 380
    height: 760
    title: "MUSE"
    color: "#1a1d23"

    // ── Properties bound to Python backend ──────────────
    property bool agentReady: backend ? backend.agentReady : false
    property bool isRecording: backend ? backend.isRecording : false
    property string currentMode: backend ? backend.currentMode : "suggest"
    property string lastOutput: backend ? backend.lastOutput : "> Awaiting input\n> Ready for composition assistance"
    property string recordingType: ""  // "voice" or "humming"

    FontLoader {
        id: monoFont
        source: "https://fonts.googleapis.com/css2?family=JetBrains+Mono"
    }

    // ── Main Content ────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        color: "#1a1d23"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 0

            // ── Header: MUSE ────────────────────────────
            Text {
                text: "M U S E"
                color: "#e8eaed"
                font.pixelSize: 18
                font.weight: Font.Bold
                font.letterSpacing: 4
                Layout.fillWidth: true
            }

            // Divider
            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: 12
                height: 1
                color: "#2d3139"
            }

            // ── Agent Status ────────────────────────────
            Row {
                Layout.topMargin: 14
                spacing: 8
                Layout.fillWidth: true

                Rectangle {
                    width: 10
                    height: 10
                    radius: 5
                    color: root.agentReady ? "#00e5ff" : "#ff5252"
                    anchors.verticalCenter: parent.verticalCenter

                    // Pulse animation when ready
                    SequentialAnimation on opacity {
                        running: root.agentReady
                        loops: Animation.Infinite
                        NumberAnimation { to: 0.4; duration: 1200; easing.type: Easing.InOutSine }
                        NumberAnimation { to: 1.0; duration: 1200; easing.type: Easing.InOutSine }
                    }
                }

                Text {
                    text: root.agentReady ? "AGENT READY" : "AGENT OFFLINE"
                    color: root.agentReady ? "#00e5ff" : "#ff5252"
                    font.pixelSize: 13
                    font.weight: Font.Bold
                    font.letterSpacing: 1.5
                }
            }

            // Divider
            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: 14
                height: 1
                color: "#2d3139"
            }

            // ── Section: INPUT MODE ─────────────────────
            Text {
                text: "INPUT MODE"
                color: "#6b7280"
                font.pixelSize: 11
                font.weight: Font.Medium
                font.letterSpacing: 1.5
                Layout.topMargin: 16
            }

            // ── Voice Prompt Card ───────────────────────
            Rectangle {
                id: voiceCard
                Layout.fillWidth: true
                Layout.topMargin: 12
                height: 88
                radius: 8
                color: (root.isRecording && root.recordingType === "voice")
                       ? "#1e3a4a" : "#22262e"
                border.color: (root.isRecording && root.recordingType === "voice")
                              ? "#00e5ff" : "#2d3139"
                border.width: 1

                Behavior on color { ColorAnimation { duration: 200 } }
                Behavior on border.color { ColorAnimation { duration: 200 } }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    hoverEnabled: true
                    onEntered: if (!root.isRecording) voiceCard.color = "#282c35"
                    onExited:  if (!root.isRecording) voiceCard.color = "#22262e"
                    onClicked: {
                        if (root.isRecording && root.recordingType === "voice") {
                            backend.stopRecording()
                        } else if (!root.isRecording) {
                            root.recordingType = "voice"
                            backend.startVoicePrompt()
                        }
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    // Microphone icon
                    Text {
                        text: "🎙"
                        font.pixelSize: 24
                        Layout.alignment: Qt.AlignTop
                    }

                    ColumnLayout {
                        spacing: 4
                        Layout.fillWidth: true

                        Text {
                            text: "VOICE PROMPT"
                            color: "#e8eaed"
                            font.pixelSize: 14
                            font.weight: Font.Bold
                            font.letterSpacing: 0.5
                        }

                        Text {
                            text: (root.isRecording && root.recordingType === "voice")
                                  ? "Recording... tap to stop"
                                  : "Describe changes in\nnatural language"
                            color: "#8b919a"
                            font.pixelSize: 13
                            lineHeight: 1.4
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }

            // Divider with MODE label
            Item {
                Layout.fillWidth: true
                Layout.topMargin: 16
                height: 14

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: modeLabel1.left
                    anchors.rightMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    height: 1
                    color: "#2d3139"
                }

                Text {
                    id: modeLabel1
                    text: "MODE"
                    color: "#6b7280"
                    font.pixelSize: 10
                    font.letterSpacing: 1.5
                    anchors.centerIn: parent
                }

                Rectangle {
                    anchors.left: modeLabel1.right
                    anchors.leftMargin: 10
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    height: 1
                    color: "#2d3139"
                }
            }

            // ── Hum Melody Card ─────────────────────────
            Rectangle {
                id: humCard
                Layout.fillWidth: true
                Layout.topMargin: 12
                height: 88
                radius: 8
                color: (root.isRecording && root.recordingType === "humming")
                       ? "#1e3a4a" : "#22262e"
                border.color: (root.isRecording && root.recordingType === "humming")
                              ? "#00e5ff" : "#2d3139"
                border.width: 1

                Behavior on color { ColorAnimation { duration: 200 } }
                Behavior on border.color { ColorAnimation { duration: 200 } }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    hoverEnabled: true
                    onEntered: if (!root.isRecording) humCard.color = "#282c35"
                    onExited:  if (!root.isRecording) humCard.color = "#22262e"
                    onClicked: {
                        if (root.isRecording && root.recordingType === "humming") {
                            backend.stopRecording()
                        } else if (!root.isRecording) {
                            root.recordingType = "humming"
                            backend.startHumming()
                        }
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    // Music note icon
                    Text {
                        text: "🎵"
                        font.pixelSize: 24
                        Layout.alignment: Qt.AlignTop
                    }

                    ColumnLayout {
                        spacing: 4
                        Layout.fillWidth: true

                        Text {
                            text: "HUM MELODY"
                            color: "#e8eaed"
                            font.pixelSize: 14
                            font.weight: Font.Bold
                            font.letterSpacing: 0.5
                        }

                        Text {
                            text: (root.isRecording && root.recordingType === "humming")
                                  ? "Recording... tap to stop"
                                  : "Sing or hum a melodic\nidea"
                            color: "#8b919a"
                            font.pixelSize: 13
                            lineHeight: 1.4
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }

            // ── Section: MODE (Suggest / Demo) ──────────
            Text {
                text: "MODE"
                color: "#6b7280"
                font.pixelSize: 11
                font.weight: Font.Medium
                font.letterSpacing: 1.5
                Layout.topMargin: 20
            }

            // Mode toggle row
            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: 8
                height: 44
                radius: 8
                color: "#22262e"

                RowLayout {
                    anchors.fill: parent
                    spacing: 0

                    // SUGGEST button
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.margins: 3
                        radius: 6
                        color: root.currentMode === "suggest" ? "#00b8d4" : "transparent"

                        Behavior on color { ColorAnimation { duration: 200 } }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: backend.setMode("suggest")
                        }

                        Text {
                            anchors.centerIn: parent
                            text: "SUGGEST"
                            color: root.currentMode === "suggest" ? "#0d1117" : "#8b919a"
                            font.pixelSize: 13
                            font.weight: Font.Bold
                            font.letterSpacing: 1
                        }
                    }

                    // DEMO button
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.margins: 3
                        radius: 6
                        color: root.currentMode === "demo" ? "#00b8d4" : "transparent"

                        Behavior on color { ColorAnimation { duration: 200 } }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: backend.setMode("demo")
                        }

                        Text {
                            anchors.centerIn: parent
                            text: "DEMO"
                            color: root.currentMode === "demo" ? "#0d1117" : "#8b919a"
                            font.pixelSize: 13
                            font.weight: Font.Bold
                            font.letterSpacing: 1
                        }
                    }
                }
            }

            // ── Section: LAST OUTPUT ────────────────────
            Text {
                text: "LAST OUTPUT"
                color: "#6b7280"
                font.pixelSize: 11
                font.weight: Font.Medium
                font.letterSpacing: 1.5
                Layout.topMargin: 20
            }

            // Output log panel
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.topMargin: 8
                Layout.minimumHeight: 100
                radius: 8
                color: "#161920"
                border.color: "#2d3139"
                border.width: 1

                Flickable {
                    id: outputFlick
                    anchors.fill: parent
                    anchors.margins: 14
                    contentHeight: outputText.implicitHeight
                    clip: true

                    Text {
                        id: outputText
                        width: outputFlick.width
                        text: root.lastOutput
                        color: "#8b919a"
                        font.pixelSize: 13
                        lineHeight: 1.5
                        wrapMode: Text.WordWrap

                        // Highlight lines starting with ">"
                        textFormat: Text.StyledText
                    }
                }

                // Auto-scroll to bottom when content changes
                Connections {
                    target: root
                    function onLastOutputChanged() {
                        outputFlick.contentY = Math.max(
                            0, outputFlick.contentHeight - outputFlick.height
                        )
                    }
                }
            }

            // ── Bottom spacer ───────────────────────────
            Item { Layout.preferredHeight: 8 }
        }
    }
}
