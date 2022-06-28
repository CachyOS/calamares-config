/* Sample of QML progress tree.
   SPDX-FileCopyrightText: 2020 Adriaan de Groot <groot@kde.org>
   SPDX-FileCopyrightText: 2021 Anke Boersma <demm@kaosx.us>
   SPDX-License-Identifier: GPL-3.0-or-later
   The progress tree (actually a list) is generally "vertical" in layout,
   with the steps going "down", but it could also be a more compact
   horizontal layout with suitable branding settings.
   This example emulates the layout and size of the widgets progress tree.
*/
import io.calamares.ui 1.0
import io.calamares.core 1.0

import QtQuick 2.3
import QtQuick.Layouts 1.3

Rectangle {
	id: sideBar;
	SystemPalette { id: myPalette; colorGroup: SystemPalette.Active }
	color: myPalette.window;
	anchors.fill: parent;
	height: 48;

	RowLayout {
		anchors.fill: parent;
		spacing: 0;
			
		Repeater {
			model: ViewManager
			Rectangle {
				Layout.leftMargin: 6;
				Layout.rightMargin: 6;
				Layout.fillWidth: true;
				radius: 6;

				Text {
					anchors.verticalCenter: parent.verticalCenter;
					anchors.horizontalCenter: parent.horizontalCenter;
					color: myPalette.text;
					font.weight: (index == ViewManager.currentStepIndex ? Font.Bold : Font.Normal);
					text: display;
				}
			}
		}

		Item {
			Layout.fillHeight: true;
		}
    }
}
