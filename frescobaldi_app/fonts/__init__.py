# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
Handle everything around (available) text fonts.
NOTE: "available" refers to the fonts that are available to LilyPond,
which may be different than for arbitrary programs and can canonically
be determined by running `lilypond -dshow-available-fonts`.
"""


from PyQt5.QtCore import (
    QObject,
    QSize
)
from PyQt5.QtWidgets import QAction

import actioncollection
import actioncollectionmanager
import icons
import plugin
import qutil

from . import musicfonts, textfonts


def fonts(mainwindow):
    return Fonts.instance(mainwindow)


class Fonts(plugin.MainWindowPlugin):

    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.fonts_document_fonts.triggered.connect(
            self.document_fonts)

    def document_fonts(self):
        """
        Menu action Document Fonts.
        Depending on the LilyPond version associated with the current document
        show either the new or the old document font dialog.
        """
        mainwin = self.mainwindow()
        view = mainwin.currentView()
        doc = mainwin.currentDocument()
        import documentinfo
        info = documentinfo.lilyinfo(doc)

        if info.version() >= (2, 19, 12):
            from . import dialog
            dlg = dialog.FontsDialog(info, mainwin)
            qutil.saveDialogSize(
                dlg, "engrave/tools/available-fonts/dialog/size",
                QSize(640, 400)
            )
            dlg.exec_()
            if dlg.result:
                cmd = (
                    dlg.result
                    if dlg.result[-1] == '\n'
                    else dlg.result + '\n'
                )
                view.textCursor().insertText(cmd)
        else:
            from . import oldfontsdialog
            dlg = oldfontsdialog.DocumentFontsDialog(self.mainwindow())
            if dlg.exec_():
                text = dlg.document_font_code()
                # NOTE: How to translate this to the dialog context?
                # if state[-1] != "paper":
                text = "\\paper {{\n{0}}}\n".format(text)
                cursor = self.mainwindow().currentView().textCursor()
                cursor.insertText(text)


class Actions(actioncollection.ActionCollection):
    name = "fonts"

    def createActions(self, parent=None):
        self.fonts_document_fonts = QAction(parent)
        self.fonts_document_fonts.setIcon(
            icons.get('preferences-desktop-font'))

    def translateUI(self):
        self.fonts_document_fonts.setText(
            _("&Document Fonts..."))
        self.fonts_document_fonts.setToolTip(
            _("Show and select text and music fonts available in the " +
              "LilyPond version of the current document"))


class AvailableFonts(QObject):
    """Store available text and music fonts for a given
    LilyPond installation. Sets for multiple registered
    installations are maintained in a global dictionary
    cached for the whole application lifetime.
    Note that the music fonts are loaded immediately while
    text fonts have to be loaded explicitly (in an
    asynchronous invocation of LilyPond)."""

    def __init__(self, lilypond_info):
        super(AvailableFonts, self).__init__()
        self.lilypond_info = lilypond_info
        self._music_fonts = musicfonts.InstalledMusicFonts(
            lilypond_info)
        self._text_fonts = textfonts.TextFonts(lilypond_info)

    def music_fonts(self):
        return self._music_fonts

    def text_fonts(self):
        return self._text_fonts


_available_fonts = {}


def available(lilypond_info):
    key = lilypond_info.abscommand() or lilypond_info.command()
    if key not in _available_fonts.keys():
        _available_fonts[key] = AvailableFonts(lilypond_info)
    return _available_fonts[key]
