import wx
import os

from . import tree_pane
from . import list_pane
from . import BUFFER_SIZE


class ESPPane(wx.SplitterWindow):

    def __init__(self, parent, main_frame):
        self.main_frame = main_frame
        wx.SplitterWindow.__init__(self, parent, -1, style=wx.SP_LIVE_UPDATE | wx.SP_3D)
        self.list_ctrl = list_pane.ESPFiles(self, main_frame)
        self.tree_ctrl = tree_pane.ESPFolders(self, main_frame)

        self.SetSashGravity(0.5)
        self.SplitVertically(self.tree_ctrl, self.list_ctrl)

    def GetDirContent(self, path):
        with self.main_frame.terminal as terminal:
            response = terminal.write('dir_contents("{0}")\r\n'.format(path))

        contents = [item.strip() for item in response.split('\n')[1:-2]]

        return contents

    def ReadFile(self, path):
        with self.main_frame.terminal as terminal:
            response = terminal.write('download_file("{0}")\r\n'.format(path))

        data = response.split('**download_file', 1)[0].split('\n', 1)[-1]
        return data

    def WriteFile(self, path, data):
        with self.main_frame.terminal as terminal:
            terminal.write('make_file_open("{0}", True)\r\n'.format(path))

            size = len(data)
            for num_bytes in range(0, size, BUFFER_SIZE - 21):
                chunk_size = min(BUFFER_SIZE - 21, size - num_bytes)
                chunk = repr(data[num_bytes: num_bytes + chunk_size])

                if not chunk.startswith("b"):
                    chunk = "b" + chunk

                terminal.write('make_file_write({0})\r\n'.format(chunk))

            terminal.write('make_file_close()\r\n'.format(path, data))

    def Exists(self, path):
        with self.main_frame.terminal as terminal:
            response = terminal.write('exists("{0}")\r\n'.format(path))

        return 'True' in response

    def MakeDirs(self, path):
        with self.main_frame.terminal as terminal:
            terminal.write('make_dirs("{0}")\r\n'.format(path))

    def ReadDirTree(self, src_path):
        res = {}

        def iter_dir(path):
            res[path] = None
            contents = self.GetDirContent(path)
            for item in contents:
                if item.endswith('<dir>'):
                    name = item.replace('<dir>', '').split('*')[0]
                    dir_path = os.path.join(path, name)
                    iter_dir(dir_path)
                else:
                    name = item.split('*')[0]
                    file_path = os.path.join(path, name)
                    res[file_path] = self.ReadFile(file_path)

        iter_dir(src_path)

        return res

    def WriteDirTree(self, dst_path, files):
        for path in sorted(list(files.keys())):
            data = files[path]
            if data is None:
                path = os.path.join(dst_path, path)
                if not self.Exists(path):
                    self.MakeDirs(path)
            else:
                path, file_name = os.path.split(path)
                path = os.path.join(dst_path, path)

                if not self.Exists(path):
                    self.MakeDirs(path)

                path = os.path.join(path, file_name)

                self.WriteFile(path, data)

    def DeleteFile(self, path):
        with self.main_frame.terminal as terminal:
            terminal.write('remove_file("{0}")\r\n'.format(path))

    def DeleteDirTree(self, path):
        with self.main_frame.terminal as terminal:
            response = terminal.write('remove_tree("{0}")\r\n'.format(path))
        response = response.split('\n')[1:-1]

        return response

    def Rename(self, src, dst):
        with self.main_frame.terminal as terminal:
            response = terminal.write('rename("{0}", "{1}")\r\n'.format(src, dst))
        if 'rename err' in response:
            return False
        return True
