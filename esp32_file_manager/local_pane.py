import wx

from . import tree_pane
from . import list_pane


class LocalPane(wx.SplitterWindow):

    def __init__(self, parent, main_frame):
        self.main_frame = main_frame
        wx.SplitterWindow.__init__(self, parent, -1, style=wx.SP_LIVE_UPDATE | wx.SP_3D)
        self.list_ctrl = list_pane.LocalFiles(self, main_frame)
        self.tree_ctrl = tree_pane.LocalFolders(self, main_frame)

        self.SetSashGravity(0.5)
        self.SplitVertically(self.tree_ctrl, self.list_ctrl)
