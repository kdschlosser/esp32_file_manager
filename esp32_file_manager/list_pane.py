import wx
import os
import time

from . import FOLDER_CLOSED_BITMAP


class MyListCtrl(wx.ListCtrl):
    def __init__(self, parent):
        wx.ListCtrl.__init__(
            self,
            parent,
            style=(
                    wx.LC_REPORT |
                    wx.LC_VIRTUAL |
                    wx.NO_FULL_REPAINT_ON_RESIZE |
                    wx.HSCROLL |
                    wx.CLIP_CHILDREN
            )
        )
        self.il = wx.ImageList(16, 16)

        self.fldridx = self.il.Add(FOLDER_CLOSED_BITMAP)
        self.fileidx = self.il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16, 16))
        )

        self.SetImageList(self.il, wx.IMAGE_LIST_NORMAL)
        self.InsertColumn(0, "Name")
        self.InsertColumn(1, "Date Modified")
        self.InsertColumn(2, "Size")

        # logger popup menu
        menu = wx.Menu()
        menu.Append(wx.ID_SELECTALL, 'Select All')
        self.Bind(wx.EVT_MENU, self.OnCmdSelectAll, id=wx.ID_SELECTALL)
        menu.AppendSeparator()
        menu.Append(wx.ID_CUT, 'Cut')
        self.Bind(wx.EVT_MENU, self.OnCmdCut, id=wx.ID_CUT)

        menu.Append(wx.ID_COPY, 'Copy')
        self.Bind(wx.EVT_MENU, self.OnCmdCopy, id=wx.ID_COPY)

        menu.Append(wx.ID_PASTE, 'Paste')
        self.Bind(wx.EVT_MENU, self.OnCmdPaste, id=wx.ID_PASTE)

        self.contextMenu = menu

        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClickEvent)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenuEvent)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnBeginDragEvent)
        self.Bind(wx.EVT_LIST_BEGIN_RDRAG, self.OnBeginRDragEvent)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnEndLabelEditEvent)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelectedEvent)

        self.data = []

    def OnContextMenuEvent(self, evt):
        self.PopupMenu(self.contextMenu, evt.GetPosition())

    def OnLeftDClickEvent(self, _):
        raise NotImplementedError

    def OnBeginDragEvent(self, _):
        raise NotImplementedError

    def OnBeginRDragEvent(self, _):
        raise NotImplementedError

    def OnEndLabelEditEvent(self, _):
        raise NotImplementedError

    def OnItemSelectedEvent(self, _):
        raise NotImplementedError

    def OnCmdCut(self, _):
        raise NotImplementedError

    def OnCmdPaste(self, _):
        raise NotImplementedError

    def OnCmdCopy(self, _):
        raise NotImplementedError

    def GetItemData(self, item):
        return self.data[item]

    def OnCmdSelectAll(self, _=None):
        for idx in range(self.GetItemCount()):
            self.Select(idx)

    def OnGetItemAttr(self, item):
        return None

    def OnGetItemImage(self, item):
        item = self.data[item]
        if item[2] == '':
            return 1

        return 2

    def OnGetItemText(self, item, column):
        return self.data[item][column]

    def OnRightUp(self, evt):
        self.PopupMenu(self.contextMenu, evt.GetPosition())

    def SetData(self, data):
        self.DeleteAllItems()
        self.data = data[:]
        self.SetItemCount(len(data))
        self.Refresh()
        self.Update()

    def RenameItem(self, src, dst):
        for item in self.data:
            if item[3] != src:
                continue

            item[3] = dst
            item[0] = os.path.split(dst)[1]
            self.Refresh()
            self.Update()
            return


class ESPFiles(MyListCtrl):

    def __init__(self, parent, main_frame):
        self.main_frame = main_frame
        MyListCtrl.__init__(self, parent)

    def OnLeftDClickEvent(self, evt):
        item, flags = self.HitTest(evt.GetPosition())

        if not flags & wx.LIST_HITTEST_ONITEM:
            return

        item = self.GetItemData(item)

        if item[2] != '':
            return

        path = item[3]

        contents = self.GetParent().GetDirContent(path)
        folders = []
        files = []
        for item in contents:
            if item.endswith('<dir>'):
                name, timestamp = item.replace('<dir>', '').split('*')
                dir_path = os.path.join(path, name)
                folders += [[name, timestamp, '', dir_path]]
            else:
                name, timestamp, size = item.split('*')
                file_path = os.path.join(path, name)
                files += [[name, timestamp, size, file_path]]

        self.SetData(folders + files)

    def OnEndLabelEditEvent(self, evt):
        if not evt.IsEditCancelled():
            item = evt.GetIndex()
            item = self.GetItemData(item)
            new_name = evt.GetLabel()
            old_name = item[0]
            if new_name == old_name:
                return
            src = item[3]
            dst = os.path.join(os.path.split(src)[0], new_name)
            if not self.GetParent().Rename(src, dst):
                return

            self.RenameItem(src, dst)
            if item[2] == '':
                self.GetParent().tree_ctrl.RenameItem(src, dst)

    def OnBeginDragEvent(self, evt):
        pass

    def OnBeginRDragEvent(self, evt):
        pass

    def OnItemSelectedEvent(self, evt):
        item = evt.GetIndex()
        item = self.GetItemData(item)

        path = item[3]

        if item[2] == '':
            self.main_frame.preview.SetValue(None, None)

        else:
            data = self.GetParent().ReadFile(path)
            self.main_frame.preview.SetValue(path, data)

    def OnCmdCut(self, _):
        pass

    def OnCmdPaste(self, _):
        pass

    def OnCmdCopy(self, _):
        text = ""
        lines = 1
        firstItem = item = self.GetNextItem(
            -1,
            wx.LIST_NEXT_ALL,
            wx.LIST_STATE_SELECTED
        )
        if item != -1:
            text = self.OnGetItemText(item, 0)[1:]
            item = self.GetNextItem(
                item,
                wx.LIST_NEXT_ALL,
                wx.LIST_STATE_SELECTED
            )
            while item != -1:
                lines += 1
                text += "\r\n" + self.OnGetItemText(item, 0)[1:]
                item = self.GetNextItem(
                    item,
                    wx.LIST_NEXT_ALL,
                    wx.LIST_STATE_SELECTED
                )
        if text != "" and wx.TheClipboard.Open():
            textDataObject = wx.TextDataObject(text)
            dataObjectComposite = wx.DataObjectComposite()
            dataObjectComposite.Add(textDataObject)
            if lines == 1:
                eventstring, icon = self.GetItemData(firstItem)[:2]
                # if icon == EVENT_ICON:
                #     customDataObject = wx.CustomDataObject("DragEventItem")
                #     customDataObject.SetData(eventstring.encode("UTF-8"))
                #     dataObjectComposite.Add(customDataObject)

            wx.TheClipboard.SetData(dataObjectComposite)
            wx.TheClipboard.Close()
            wx.TheClipboard.Flush()

    def OnStartDrag(self, event):
        idx = event.GetIndex()
        itemData = self.GetItemData(idx)
        # if itemData[1] != EVENT_ICON:
        #     return
        text = itemData[2]
        # create our own data format and use it in a
        # custom data object
        customData = wx.CustomDataObject(wx.CustomDataFormat("DragItem"))
        customData.SetData(text.encode("utf-8"))

        # And finally, create the drop source and begin the drag
        # and drop operation
        dropSource = wx.DropSource(self)
        dropSource.SetData(customData)
        result = dropSource.DoDragDrop(wx.Drag_AllowMove)
        if result == wx.DragMove:
            self.Refresh()


class LocalFiles(MyListCtrl):

    def __init__(self, parent, main_frame):
        self.main_frame = main_frame
        MyListCtrl.__init__(self, parent)

    def OnLeftDClickEvent(self, evt):
        item, flags = self.HitTest(evt.GetPosition())

        if not flags & wx.LIST_HITTEST_ONITEM:
            return

        item = self.GetItemData(item)

        if item[2] != '':
            return

        path = item[3]

        files = []
        folders = []

        for name in os.listdir(path):
            f_path = os.path.join(path, name)
            stats = os.stat(f_path)
            timestamp = time.strftime("%m/%d/%Y %I:%M %p", time.localtime(stats.st_mtime))

            if os.path.isdir(f_path):
                folders += [[name, timestamp, '', f_path]]
            else:
                size = str(stats.st_size)
                files += [[name, timestamp, size, f_path]]

        self.SetData(folders + files)

    def OnEndLabelEditEvent(self, evt):
        if not evt.IsEditCancelled():
            item = evt.GetIndex()
            item = self.GetItemData(item)
            new_name = evt.GetLabel()
            old_name = item[0]
            if new_name == old_name:
                return
            src = item[3]
            dst = os.path.join(os.path.split(src)[0], new_name)
            os.rename(src, dst)

            self.RenameItem(src, dst)
            if item[2] == '':
                self.GetParent().tree_ctrl.RenameItem(src, dst)

    def OnBeginDragEvent(self, evt):
        pass

    def OnBeginRDragEvent(self, evt):
        pass

    def OnItemSelectedEvent(self, evt):
        item = evt.GetIndex()
        item = self.GetItemData(item)

        path = item[3]

        if item[2] == '':
            self.main_frame.preview.SetValue(None, None)

        else:
            with open(path, 'rb') as f:
                data = f.read()

            self.main_frame.preview.SetValue(path, data)

    def OnCmdCut(self, _):
        pass

    def OnCmdPaste(self, _):
        pass

    def OnCmdCopy(self, _):
        text = ""
        lines = 1
        firstItem = item = self.GetNextItem(
            -1,
            wx.LIST_NEXT_ALL,
            wx.LIST_STATE_SELECTED
        )
        if item != -1:
            text = self.OnGetItemText(item, 0)[1:]
            item = self.GetNextItem(
                item,
                wx.LIST_NEXT_ALL,
                wx.LIST_STATE_SELECTED
            )
            while item != -1:
                lines += 1
                text += "\r\n" + self.OnGetItemText(item, 0)[1:]
                item = self.GetNextItem(
                    item,
                    wx.LIST_NEXT_ALL,
                    wx.LIST_STATE_SELECTED
                )
        if text != "" and wx.TheClipboard.Open():
            textDataObject = wx.TextDataObject(text)
            dataObjectComposite = wx.DataObjectComposite()
            dataObjectComposite.Add(textDataObject)
            if lines == 1:
                eventstring, icon = self.GetItemData(firstItem)[:2]
                # if icon == EVENT_ICON:
                #     customDataObject = wx.CustomDataObject("DragEventItem")
                #     customDataObject.SetData(eventstring.encode("UTF-8"))
                #     dataObjectComposite.Add(customDataObject)

            wx.TheClipboard.SetData(dataObjectComposite)
            wx.TheClipboard.Close()
            wx.TheClipboard.Flush()

    def OnStartDrag(self, event):
        idx = event.GetIndex()
        itemData = self.GetItemData(idx)
        # if itemData[1] != EVENT_ICON:
        #     return
        text = itemData[2]
        # create our own data format and use it in a
        # custom data object
        customData = wx.CustomDataObject(wx.CustomDataFormat("DragItem"))
        customData.SetData(text.encode("utf-8"))

        # And finally, create the drop source and begin the drag
        # and drop operation
        dropSource = wx.DropSource(self)
        dropSource.SetData(customData)
        result = dropSource.DoDragDrop(wx.Drag_AllowMove)
        if result == wx.DragMove:
            self.Refresh()
