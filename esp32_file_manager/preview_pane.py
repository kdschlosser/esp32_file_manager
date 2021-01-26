import wx
import os


IMAGE_EXTENSIONS = (
    '.png', '.gif', '.jpg', '.jpeg', '.tiff', '.tif',
    '.bmp', '.dib', '.pcx', '.tga',  '.icb',  '.vda',
    '.vst', '.iff', '.xpm', '.ico',  '.cur',  '.ani'
)


TEXT_EXTENSIONS = (
    '.html', '.htm', '.txt', '.py', '.css', '.js', '.md'
)


class PreviewPane(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style=wx.BORDER_NONE)
        self.ctrl = None
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        v_sizer.Add(self.sizer, 1, wx.ALL | wx.EXPAND, 10)
        self.SetSizer(v_sizer)

    def SetValue(self, filename, data):
        if filename is None:
            if self.ctrl is not None:
                self.sizer.Hide(self.ctrl)
                self.ctrl.Destroy()
                self.sizer.Layout()
                self.Fit()
                self.ctrl = None
        else:
            ext = os.path.splitext(filename)[-1]
            if ext in IMAGE_EXTENSIONS:
                image = wx.Image(data)
                bmp = image.ConvertToBitmap()
                if isinstance(self.ctrl, wx.StaticBitmap):
                    self.ctrl.SetBitmap(bmp)
                else:
                    if self.ctrl is not None:
                        self.sizer.Hide(self.ctrl)
                        self.ctrl.Destroy()

                    self.ctrl = wx.StaticBitmap(self, -1, bmp)
                    self.sizer.Add(self.ctrl, 1, wx.EXPAND)
                    self.sizer.Layout()
                    self.Fit()

            elif ext in TEXT_EXTENSIONS:
                data = data.replace('\r\r\n', '\r\n')
                if isinstance(self.ctrl, wx.TextCtrl):
                    self.ctrl.SetValue(data)
                else:
                    if self.ctrl is not None:
                        self.sizer.Hide(self.ctrl)
                        self.ctrl.Destroy()

                    self.ctrl = wx.TextCtrl(
                        self,
                        -1,
                        data,
                        style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_DONTWRAP
                    )
                    self.sizer.Add(self.ctrl, 1, wx.EXPAND)
                    self.sizer.Layout()
                    self.Fit()
