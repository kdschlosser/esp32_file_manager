import sys
import wx
import os
import time

__version__ = '1.0.0'
BUFFER_SIZE = 32
_debug = False
BASE_PATH = os.path.dirname(__file__)

DEVICE_IDS = (
    #  (VID, PID)
    (0x10C4, 0xEA60),  # Silicon Labs CP210x USB to UART Bridge
)


def DEBUG(txt):
    if _debug:
        print(txt)


app = wx.GetApp()

if app is None:
    _mainloop = True
    app = wx.App()
else:
    _mainloop = False


FOLDER_OPEN_BITMAP = wx.Image(
    os.path.join(BASE_PATH, 'images', 'folder_open.png')
).Rescale(16, 16).ConvertToBitmap()

FOLDER_CLOSED_BITMAP = wx.Image(
    os.path.join(BASE_PATH, 'images', 'folder_closed.png')
).Rescale(16, 16).ConvertToBitmap()


HITTEST_FLAGS = (
    wx.TREE_HITTEST_ONITEMLABEL |
    wx.TREE_HITTEST_ONITEMICON |
    wx.TREE_HITTEST_ONITEMRIGHT
)

from . import serial  # NOQA
from . import esp_pane  # NOQA
from . import local_pane  # NOQA
from . import terminal_pane  # NOQA
from . import preview_pane  # NOQA
from . import drag_n_drop  # NOQA


class Frame(wx.Frame):

    def __init__(self, port=None, baudrate=115200):
        if port is None:
            port = serial.Serial.get_port()

        if port is None:
            print('Unable to detect port you will have to use the -p switch and specify the port')
            sys.exit(1)

        self.serial = serial.Serial()
        wx.Frame.__init__(self, None, -1, size=(1600, 800))

        splitter1 = wx.SplitterWindow(self, -1, style=wx.SP_LIVE_UPDATE | wx.SP_3D)
        splitter2 = wx.SplitterWindow(splitter1, -1, style=wx.SP_LIVE_UPDATE | wx.SP_3D)
        splitter3 = wx.SplitterWindow(splitter2, -1, style=wx.SP_LIVE_UPDATE | wx.SP_3D)

        self.terminal = terminal_pane.TerminalPane(splitter1, sp)

        self.local_pane = local_pane.LocalPane(splitter2, self)
        self.esp32_pane = esp_pane.ESPPane(splitter3, self)
        self.preview = preview_pane.PreviewPane(splitter3)

        local_tree = self.local_pane.tree_ctrl
        esp32_tree = self.esp32_pane.tree_ctrl

        esp32_tree.Bind(wx.EVT_TREE_BEGIN_RDRAG, self.OnBeginRightDrag)
        esp32_tree.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnBeginLeftDrag)

        local_tree.Bind(wx.EVT_TREE_BEGIN_RDRAG, self.OnBeginRightDrag)
        local_tree.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnBeginLeftDrag)

        v_sizer = wx.BoxSizer(wx.VERTICAL)
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(splitter1, 1, wx.EXPAND | wx.ALL, 10)
        v_sizer.Add(h_sizer, 1, wx.EXPAND)

        self.SetSizer(v_sizer)
        self.drag_source = None

        splitter1.SetSashGravity(0.50)
        splitter2.SetSashGravity(0.33)
        splitter3.SetSashGravity(0.50)

        splitter1.SplitHorizontally(splitter2, self.terminal)
        splitter2.SplitVertically(self.local_pane, splitter3)
        splitter3.SplitVertically(self.esp32_pane, self.preview)

    def Show(self, flag=True):
        wx.Frame.Show(self, flag)
        if flag:
            boot_data = self.serial.init()

            for line in boot_data.split('\n'):
                self.terminal.AppendText(line + '\n')
                time.sleep(0.02)

    def OnBeginLeftDrag(self, event):
        '''Allow drag-and-drop for leaf nodes.'''
        tree = event.GetEventObject()

        srcItemId = event.GetItem()
        tree.SelectItem(srcItemId)
        dropTarget = tree.drop_target
        dropTarget.source = srcItemId
        dropTarget.left_drag = True
        self.drag_source = tree
        drag_n_drop.DropSource(self, b"1").DoDragDrop(wx.Drag_AllowMove)
        self.drag_source = None
        dropTarget.source = None
        dropTarget.lastTargetItemId = None

        if dropTarget.lastHighlighted is not None:
            tree.SetItemDropHighlight(dropTarget.lastHighlighted, False)
            dropTarget.lastHighlighted = None

    def OnBeginRightDrag(self, event):
        '''Allow drag-and-drop for leaf nodes.'''
        tree = event.GetEventObject()

        srcItemId = event.GetItem()
        tree.SelectItem(srcItemId)
        dropTarget = tree.drop_target
        dropTarget.source = srcItemId
        dropTarget.left_drag = False
        self.drag_source = tree

        drag_n_drop.DropSource(self, b"1").DoDragDrop(wx.Drag_AllowMove)
        self.drag_source = None
        dropTarget.source = None
        dropTarget.lastTargetItemId = None

        if dropTarget.lastHighlighted is not None:
            tree.SetItemDropHighlight(dropTarget.lastHighlighted, False)
            dropTarget.lastHighlighted = None


def main():
    global _debug

    port = None
    baudrate = 115200

    for i, arg in enumerate(sys.argv[1:]):
        if arg == '-p':
            port = sys.argv[i + 1]
        elif arg == '-b':
            baudrate = int(sys.argv[i + 1])
        elif arg == '-d':
            _debug = True

    frame = Frame(port=port, baudrate=baudrate)
    frame.Show()
    if _mainloop:
        app.MainLoop()
