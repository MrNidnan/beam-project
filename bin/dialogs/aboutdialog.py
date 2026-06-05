#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright (C) 2014 Mikael Holber http://http://www.beam-project.com
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Beam; if not, write to the Free Software Foundation,
#    Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#    or download it from http://www.gnu.org/licenses/gpl.txt
#
# This Python file uses the following encoding: utf-8

import webbrowser
import wx
import wx.html

from bin.beamsettings import beamSettings

##################################################
# About DIALOG
##################################################


class _HtmlWindow(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())


def ShowAboutDialog(parent):
    s = beamSettings.getString
    dlg = wx.Dialog(parent, title="About Beam", size=(520, 480),
                    style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

    html = _HtmlWindow(dlg)
    html.SetPage(_build_html(s))

    btn = wx.Button(dlg, wx.ID_OK, "Close")
    btn.SetDefault()

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(html, 1, wx.EXPAND | wx.ALL, 8)
    sizer.Add(btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
    dlg.SetSizer(sizer)
    dlg.Layout()

    dlg.ShowModal()
    dlg.Destroy()


def _build_html(s):
    return """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; margin: 12px; font-size: 11pt;">

<h2 style="margin-bottom: 2px;">Beam &nbsp; <small style="color:#666;">v{version}</small></h2>
<p style="color:#444;">{copyright}</p>

<p>{description}</p>

<h3>Links</h3>
<ul>
  <li><a href="{github}">Documentation &amp; setup (GitHub)</a></li>
  <li><a href="{facebook}">Facebook</a></li>
  <li><a href="{website}">Old Project website</a></li>
  <li><a href="{bitbucket}">Legacy wiki on Bitbucket (reference)</a></li>
</ul>

<h3>Developers</h3>
<p>{developer}</p>
<p><a href="{authors}">Full authors list (AUTHORS.md)</a></p>

<h3>License</h3>
<p style="font-size:9pt; color:#555;">{license}</p>

<h3>Credits</h3>
<p>{artist}</p>

</body>
</html>""".format(
        version=s("version"),
        copyright=s("aboutcopyright"),
        description=s("aboutdialogdescription"),
        github=s("aboutgithub"),
        facebook=s("aboutfacebook"),
        website=s("aboutwebsite"),
        bitbucket=s("aboutbitbucket"),
        developer=s("aboutdeveloper").replace("\n", "<br>"),
        authors=s("aboutauthors"),
        license=s("aboutdialoglicense"),
        artist=s("aboutartist"),
    )
