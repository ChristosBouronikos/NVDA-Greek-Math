# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 3 or later.
# See the file COPYING.txt for more details.
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
# Project contact: Bouronikos Christos <chrisbouronikos@gmail.com>
# GitHub: https://github.com/ChristosBouronikos
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos

"""The dialog that downloads and removes optional neural voices."""

import threading

import addonHandler
import gui
import ui
import wx
from logHandler import log

from .neural.manager import VoiceManager

addonHandler.initTranslation()

#: Columns of the voice list, in display order.
_COLUMNS = (
	# Translators: Column heading: the name of a downloadable voice.
	(_("Voice"), 280),
	# Translators: Column heading: which languages a voice can speak.
	(_("Languages"), 110),
	# Translators: Column heading: how large the download is.
	(_("Download"), 90),
	# Translators: Column heading: the licence covering a voice model.
	(_("Licence"), 130),
	# Translators: Column heading: whether a voice is downloaded.
	(_("Status"), 120),
)


class DownloadProgressDialog(wx.Dialog):
	"""A cancellable progress dialog driven from a worker thread."""

	def __init__(self, parent, title):
		super().__init__(parent, title=title, style=wx.CAPTION | wx.SYSTEM_MENU)
		self.cancelled = False
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.label = wx.StaticText(self, label=_("Preparing…"))
		sizer.Add(self.label, flag=wx.ALL | wx.EXPAND, border=10)
		self.gauge = wx.Gauge(self, range=100, size=(360, 20))
		# Translators: Accessible name of the download progress bar.
		self.gauge.SetName(_("Download progress"))
		sizer.Add(self.gauge, flag=wx.ALL | wx.EXPAND, border=10)
		self.cancelButton = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
		self.cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
		sizer.Add(self.cancelButton, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
		self.SetSizerAndFit(sizer)

	def onCancel(self, event):
		self.cancelled = True
		self.label.SetLabel(_("Cancelling…"))
		self.cancelButton.Disable()

	def update(self, done, total):
		"""Called from the worker thread; marshals onto the GUI thread."""
		if total:
			percent = int(done * 100 / total)
			wx.CallAfter(self.gauge.SetValue, min(100, percent))
			wx.CallAfter(
				self.label.SetLabel,
				# Translators: Download progress. {done} and {total} are megabyte counts.
				_("Downloaded {done:.0f} MB of {total:.0f} MB").format(
					done=done / 1000000.0, total=total / 1000000.0
				),
			)
		return not self.cancelled


class NeuralVoicesDialog(wx.Dialog):
	"""Lists the catalogue and installs or removes voices."""

	def __init__(self, parent):
		# Translators: Title of the neural voice manager dialog.
		super().__init__(parent, title=_("Neural voices"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.manager = VoiceManager()
		self.voices = []

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		helper = gui.guiHelper.BoxSizerHelper(self, sizer=mainSizer)

		self.statusText = helper.addItem(wx.StaticText(self, label=""))

		self.list = helper.addItem(
			wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL, size=(720, 260))
		)
		# Translators: Accessible name of the list of downloadable voices.
		self.list.SetName(_("Available voices"))
		for index, (heading, width) in enumerate(_COLUMNS):
			self.list.InsertColumn(index, heading, width=width)
		self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectionChanged)
		self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onSelectionChanged)

		self.notesText = helper.addItem(wx.StaticText(self, label="", size=(720, 60)))

		buttons = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Button that downloads the selected voice.
		self.downloadButton = wx.Button(self, label=_("&Download"))
		self.downloadButton.Bind(wx.EVT_BUTTON, self.onDownload)
		buttons.Add(self.downloadButton, flag=wx.RIGHT, border=8)
		# Translators: Button that deletes a downloaded voice.
		self.removeButton = wx.Button(self, label=_("&Remove"))
		self.removeButton.Bind(wx.EVT_BUTTON, self.onRemove)
		buttons.Add(self.removeButton, flag=wx.RIGHT, border=8)
		# Translators: Button that closes the neural voice dialog.
		closeButton = wx.Button(self, wx.ID_CLOSE, _("&Close"))
		closeButton.Bind(wx.EVT_BUTTON, lambda event: self.Close())
		buttons.Add(closeButton)
		helper.addItem(buttons)

		self.SetEscapeId(wx.ID_CLOSE)
		self.SetSizerAndFit(mainSizer)
		self.refresh()
		self.list.SetFocus()

	# -- display -------------------------------------------------------------

	def refresh(self):
		try:
			self.voices = list(self.manager.catalogue.voices)
		except Exception:
			log.error("greekMathReader: could not read the voice catalogue", exc_info=True)
			self.voices = []
		self.list.DeleteAllItems()
		for voice in self.voices:
			row = self.list.InsertItem(self.list.GetItemCount(), voice.label)
			self.list.SetItem(row, 1, ", ".join(voice.languages))
			self.list.SetItem(row, 2, _("{size:.0f} MB").format(size=voice.sizeMegabytes))
			self.list.SetItem(row, 3, voice.licenseName or voice.licenseId)
			self.list.SetItem(
				row,
				4,
				# Translators: Shown when a voice has been downloaded.
				_("Downloaded")
				if self.manager.isVoiceInstalled(voice.id)
				# Translators: Shown when a voice has not been downloaded.
				else _("Not downloaded"),
			)
		if self.voices and self.list.GetFirstSelected() < 0:
			self.list.Select(0)
			self.list.Focus(0)
		self.updateStatus()
		self.onSelectionChanged(None)

	def updateStatus(self):
		if not self.manager.isPlatformSupported():
			# Translators: Shown when no prebuilt speech runtime exists for this NVDA build.
			self.statusText.SetLabel(
				_(
					"No speech runtime is available for this NVDA build ({platform}). "
					"Neural voices cannot be used here."
				).format(platform=self.manager.platformKey)
			)
			return
		used = self.manager.diskUsage()
		if self.manager.isRuntimeInstalled():
			# Translators: Status line. {size} is a megabyte count.
			text = _("Speech runtime installed. Downloaded data uses {size:.0f} MB.").format(
				size=used / 1000000.0
			)
		else:
			# Translators: Status line shown before anything has been downloaded.
			text = _(
				"The speech runtime (about 19 MB) will be downloaded automatically "
				"with your first voice."
			)
		self.statusText.SetLabel(text)

	def selectedVoice(self):
		index = self.list.GetFirstSelected()
		if index < 0 or index >= len(self.voices):
			return None
		return self.voices[index]

	def onSelectionChanged(self, event):
		voice = self.selectedVoice()
		if voice is None:
			self.notesText.SetLabel("")
			self.downloadButton.Enable(False)
			self.removeButton.Enable(False)
			return
		installed = self.manager.isVoiceInstalled(voice.id)
		self.notesText.SetLabel(voice.notes)
		self.downloadButton.Enable(not installed and self.manager.isPlatformSupported())
		self.removeButton.Enable(installed)

	# -- actions -------------------------------------------------------------

	def _confirmLicence(self, voice):
		"""Ask the user to accept a licence that binds them personally."""
		if not voice.requiresLicenseAcceptance:
			return True
		message = _(
			"{label} is published under the {licence} licence.\n\n"
			"Unlike the other voices offered here, this licence places conditions on "
			"how the model may be used and requires anyone you pass it on to receive "
			"the same conditions. That is why this add-on cannot include it, and why "
			"you are downloading it yourself.\n\n"
			"Licence: {url}\n\n"
			"Do you accept these terms and want to download it?"
		).format(label=voice.label, licence=voice.licenseName, url=voice.licenseUrl)
		with wx.MessageDialog(
			self,
			message,
			# Translators: Title of the licence acceptance prompt.
			_("Accept the licence?"),
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
		) as dialog:
			return dialog.ShowModal() == wx.ID_YES

	def onDownload(self, event):
		voice = self.selectedVoice()
		if voice is None or not self._confirmLicence(voice):
			return
		needsRuntime = not self.manager.isRuntimeInstalled()
		progress = DownloadProgressDialog(
			self,
			# Translators: Title of the download dialog. {label} is a voice name.
			_("Downloading {label}").format(label=voice.label),
		)
		result = {}

		def work():
			try:
				if needsRuntime and not self.manager.installRuntime(progress=progress.update):
					result["error"] = self.manager.lastError
				elif not self.manager.installVoice(voice.id, progress=progress.update):
					result["error"] = self.manager.lastError
			except Exception as error:  # pragma: no cover - defensive
				log.error("greekMathReader: voice download failed", exc_info=True)
				result["error"] = str(error)
			wx.CallAfter(progress.EndModal, wx.ID_OK)

		threading.Thread(target=work, daemon=True).start()
		progress.ShowModal()
		progress.Destroy()

		error = result.get("error")
		if progress.cancelled and error:
			# Translators: Spoken after the user cancels a download.
			ui.message(_("Download cancelled."))
		elif error:
			gui.messageBox(
				# Translators: Error shown when a voice could not be downloaded.
				_("{label} could not be downloaded.\n\n{reason}").format(
					label=voice.label, reason=error
				),
				# Translators: Title of the download failure message.
				_("Download failed"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
		else:
			gui.messageBox(
				# Translators: Shown after a voice downloads successfully.
				_(
					"{label} is ready.\n\n"
					"To use it, choose \"Greek Math Reader neural voices\" as your "
					"synthesizer in NVDA's Speech settings."
				).format(label=voice.label),
				# Translators: Title of the download success message.
				_("Voice installed"),
				wx.OK | wx.ICON_INFORMATION,
				self,
			)
		self.refresh()

	def onRemove(self, event):
		voice = self.selectedVoice()
		if voice is None:
			return
		with wx.MessageDialog(
			self,
			# Translators: Confirmation before deleting a downloaded voice.
			_("Remove {label} and free {size:.0f} MB?").format(
				label=voice.label, size=voice.sizeMegabytes
			),
			# Translators: Title of the removal confirmation.
			_("Remove voice?"),
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
		) as dialog:
			if dialog.ShowModal() != wx.ID_YES:
				return
		if self.manager.removeVoice(voice.id):
			# Translators: Spoken after a voice is deleted.
			ui.message(_("Voice removed."))
		else:
			gui.messageBox(
				# Translators: Error shown when a voice could not be deleted.
				_("The voice could not be removed.\n\n{reason}").format(
					reason=self.manager.lastError
				),
				# Translators: Title of the removal failure message.
				_("Removal failed"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
		self.refresh()
