import wx
import threading

if not wx.GetApp():
    app = wx.App()


ColourDatabase = wx.ColourDatabase()

FOREGROUND_COLOURS = {
    30: wx.BLACK,
    31: wx.RED,
    32: wx.YELLOW,
    33: wx.YELLOW,
    34: wx.BLUE,
    35: ColourDatabase.Find('MAGENTA'),
    36: wx.CYAN,
    37: wx.WHITE,
    39: wx.GREEN
}

BACKGROUND_COLOURS = {
    40: wx.WHITE,
    41: wx.RED,
    42: wx.GREEN,
    43: wx.YELLOW,
    44: wx.BLUE,
    45: ColourDatabase.Find('MAGENTA'),
    46: wx.CYAN,
    47: wx.WHITE,
    49: wx.BLACK
}


class TerminalPane(wx.SplitterWindow):

    def __init__(self, parent, serial):
        wx.SplitterWindow.__init__(self, parent, -1, style=wx.SP_LIVE_UPDATE | wx.SP_3D)

        self.serial = serial

        self.text_ctrl1 = wx.TextCtrl(
            self,
            -1,
            '',
            style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_DONTWRAP | wx. TE_RICH
        )
        self.text_ctrl1.SetForegroundColour(wx.Colour(0, 255, 0))
        self.text_ctrl1.SetBackgroundColour(wx.Colour(0, 0, 0))

        self.text_ctrl2 = wx.TextCtrl(
            self,
            -1,
            '',
            style=wx.TE_MULTILINE | wx.TE_DONTWRAP | wx.TE_PROCESS_ENTER | wx.TE_PROCESS_TAB
        )
        self.text_ctrl2.SetForegroundColour(wx.Colour(0, 255, 0))
        self.text_ctrl2.SetBackgroundColour(wx.Colour(0, 0, 0))

        font = self.text_ctrl1.GetFont()
        self.text_attr = wx.TextAttr()
        self.text_attr.SetFont(font)
        self.text_attr.SetTextColour(wx.GREEN)
        self.text_attr.SetBackgroundColour(wx.BLACK)

        self.SplitHorizontally(self.text_ctrl1, self.text_ctrl2)
        self.SetSashGravity(0.75)

        self.text_ctrl2.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        self.serial_lock = threading.Lock()
        self._exit_event = threading.Event()
        self._thread = threading.Thread(target=self.serial_read_loop)

    def AppendText(self, text):
        print(repr(text))
        text_attr = wx.TextAttr(self.text_attr)
        text_len = len(self.text_ctrl1.GetValue())
        self.text_ctrl1.SetInsertionPointEnd()

        if '\x1b[' in text:
            text = [item.split('m', 1) for item in text.split('\x1b[') if item]
            print(text)
            for item in text:
                if len(item) == 1:
                    item = ['0', item[0]]
                    
                ansi_codes, chars = item
                text_attr = wx.TextAttr(text_attr)
                ansi_codes = [int(item) for item in ansi_codes.split(';')]
                for code in ansi_codes:
                    if code == 0:
                        text_attr.SetFontStyle(wx.FONTSTYLE_NORMAL)
                        text_attr.SetFontWeight(wx.FONTWEIGHT_NORMAL)
                        text_attr.SetFontUnderlined(False)
                        text_attr.SetTextColour(wx.GREEN)
                        text_attr.SetBackgroundColour(wx.BLACK)
                    elif code == 3:
                        text_attr.SetFontStyle(wx.FONTSTYLE_ITALIC)
                    elif code == 23:
                        text_attr.SetFontStyle(wx.FONTSTYLE_NORMAL)
                    elif code == 4:
                        text_attr.SetFontUnderlined(True)
                        text_attr.SetFontUnderlineType(wx.TEXT_ATTR_UNDERLINE_SOLID)
                    elif code == 21:
                        text_attr.SetFontUnderlined(True)
                        text_attr.SetFontUnderlineType(wx.TEXT_ATTR_UNDERLINE_DOUBLE)
                    elif code == 24:
                        text_attr.SetFontUnderlined(False)
                    elif code == 1:
                        text_attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
                    elif code == 22:
                        text_attr.SetFontWeight(wx.FONTWEIGHT_NORMAL)
                    elif code == 2:
                        text_attr.SetFontWeight(wx.FONTWEIGHT_EXTRALIGHT)
                    elif code in FOREGROUND_COLOURS:
                        text_attr.SetTextColour(FOREGROUND_COLOURS[code])
                    elif code in BACKGROUND_COLOURS:
                        text_attr.SetBackgroundColour(BACKGROUND_COLOURS[code])

                print(text_attr.GetTextColour())
                print(text_attr.GetBackgroundColour())

                self.text_ctrl1.AppendText(chars)
                self.text_ctrl1.SetStyle(text_len, text_len + len(chars), text_attr)
                text_len += len(chars)
        else:
            self.text_ctrl1.AppendText(text)
            self.text_ctrl1.SetStyle(text_len, text_len + len(text), text_attr)

        self.text_attr = text_attr
        self.text_ctrl1.SetInsertionPointEnd()

    def read(self):
        return self.serial.read_decoded()

    def write(self, data):
        return self.serial.communicate(data)

    def __enter__(self):
        self.serial_lock.acquire()
        self.text_ctrl2.Enable(False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.serial_lock.release()
        self.text_ctrl2.Enable()

    def serial_read_loop(self):
        while not self._exit_event.is_set():
            with self.serial_lock:
                data = self.read()
                if data:
                    def _do(dta):
                        self.AppendText(dta)

                    wx.CallAfter(_do, data)

    def on_enter(self, evt):
        if self.serial_lock.locked():
            return

        value = self.text_ctrl2.GetValue()
        lines = value.split('\n')
        last_line = lines[-1]
        if (
            not last_line.startswith(' ') and
            not last_line.startswith('\t') and
            not last_line.endswith('/') and
            not last_line.endswith(':')
        ):
            for o_brace, c_brace in (('(', ')'), ('[', ']'), ('{', '}')):
                brace_count = value.count(o_brace) - value.count(c_brace)
                if brace_count > 0:
                    evt.Skip()
                    break
            else:
                self.serial.write(bytes(value + '\r\n', encoding='utf-8'))
                self.text_ctrl2.SetValue('')
        else:
            evt.Skip()
