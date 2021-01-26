import wx
import os
import time
import send2trash

from . import FOLDER_CLOSED_BITMAP, FOLDER_OPEN_BITMAP
from .drag_n_drop import DropTarget


class MyTreeCtrl(wx.TreeCtrl):
    main_frame = None

    def __init__(self, parent):
        wx.TreeCtrl.__init__(self, parent, -1, style=wx.TR_HAS_BUTTONS | wx.TR_EDIT_LABELS)
        self.il = wx.ImageList(16, 16)

        self.fldridx = self.il.Add(FOLDER_CLOSED_BITMAP)
        self.fldropenidx = self.il.Add(FOLDER_OPEN_BITMAP)
        self.fileidx = self.il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16, 16))
        )

        self.SetImageList(self.il)
        self.drop_target = DropTarget(self)
        self.SetDropTarget(self.drop_target)

        self.Bind(wx.EVT_TREE_DELETE_ITEM, self.OnItemDeleteEvent)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemActivateEvent)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnItemExpandingEvent)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClickEvent)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelectionChangedEvent)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndLabelEditEvent)

        self.context_menu = menu = wx.Menu()
        menu.Append(wx.ID_COPY, 'Copy')
        menu.Append(wx.ID_CUT, 'Cut')
        menu.Append(wx.ID_PASTE, 'Paste')
        menu.AppendSeparator()
        menu.Append(wx.ID_DELETE, 'Delete')

        menu.Bind(wx.EVT_MENU, self.OnItemCopyEvent, id=wx.ID_COPY)
        menu.Bind(wx.EVT_MENU, self.OnItemCutEvent, id=wx.ID_CUT)
        menu.Bind(wx.EVT_MENU, self.OnItemPasteEvent, id=wx.ID_PASTE)
        menu.Bind(wx.EVT_MENU, self.OnItemDeleteEvent, id=wx.ID_DELETE)

    def OnEndLabelEditEvent(self, _):
        raise NotImplementedError

    def OnItemExpandingEvent(self, evt):
        tree_item = evt.GetItem()
        if not self.IsExpanded(tree_item):
            self.AddChildren(tree_item)

    def OnItemActivateEvent(self, evt):
        tree_item = evt.GetItem()
        if tree_item.IsOk():
            if not self.IsExpanded(tree_item):
                self.Expand(tree_item)

            self.main_frame.preview.SetValue(None, None)
            files_folders = self.AddChildren(tree_item)
            self.GetParent().list_ctrl.SetData(files_folders)

    def OnItemCopyEvent(self, evt):
        raise NotImplementedError

    def OnItemCutEvent(self, evt):
        raise NotImplementedError

    def OnItemPasteEvent(self, evt):
        raise NotImplementedError

    def OnItemDeleteEvent(self, evt):
        raise NotImplementedError

    def OnItemMenuEvent(self, evt):
        """
        Handles wx.EVT_TREE_ITEM_MENU
        """
        tree_item = evt.GetItem()

        if self.GetRootItem() == tree_item:
            self.context_menu.Enable(wx.ID_DELETE, False)
        else:
            self.context_menu.Enable(wx.ID_DELETE, True)

        self.PopupMenu(self.context_menu, evt.GetPoint())
        evt.Skip()

    def OnBeginLabelEditEvent(self, evt):
        """
        Handles wx.EVT_TREE_BEGIN_LABEL_EDIT
        """
        tree_item = evt.GetItem()
        if tree_item == self.GetRootItem():
            evt.Veto()
            return

        evt.Skip()

    def OnRightClickEvent(self, evt):
        """
        Handles wx.EVT_TREE_ITEM_RIGHT_CLICK
        """
        tree_item = evt.GetItem()
        self.SelectItem(tree_item)

    def OnSelectionChangedEvent(self, evt):
        """
        Handles wx.EVT_TREE_SEL_CHANGED
        """
        tree_item = evt.GetItem()

        files_folders = self.AddChildren(tree_item)
        self.GetParent().list_ctrl.SetData(files_folders)
        self.main_frame.preview.SetValue(None, None)
        evt.Skip()

    def AddChildren(self, _):
        raise NotImplementedError

    def Traverse(self, func, startNode):
        """Apply 'func' to each node in a branch, beginning with 'startNode'. """

        def TraverseAux(node, depth, fnc):
            nc = self.GetChildrenCount(node, 0)
            child, cookie = self.GetFirstChild(node)
            # In wxPython 2.5.4, GetFirstChild only takes 1 argument
            for i in range(nc):
                fnc(child, depth)
                TraverseAux(child, depth + 1, fnc)
                child, cookie = self.GetNextChild(node, cookie)

        func(startNode, 0)
        TraverseAux(startNode, 1, func)

    def ItemIsChildOf(self, item1, item2):
        result = [False]

        def test_func(node, _):
            if node == item1:
                result[0] = True

        self.Traverse(test_func, item2)
        return result

    def SaveItemsToList(self, startnode):
        lst = []

        def save_func(node, depth):
            tmplist = lst
            for x in range(depth):
                if type(tmplist[-1]) is not dict:
                    tmplist.append({})
                tmplist = tmplist[-1].setdefault('children', [])

            item = dict(
                label=self.GetItemText(node),
                data=self.GetItemData(node),
                icon_normal=self.GetItemImage(node),
                icon_selected=self.GetItemImage(node, wx.TreeItemIcon_Selected),
                icon_expanded=self.GetItemImage(node, wx.TreeItemIcon_Expanded),
                icon_selectedexpanded=self.GetItemImage(node, wx.TreeItemIcon_SelectedExpanded)
            )
            tmplist.append(item)

        self.Traverse(save_func, startnode)
        return lst

    def InsertItemsFromList(self, itemlist, parent, insertafter=None, appendafter=False):
        newitems = []
        for item in itemlist:
            if insertafter:
                node = self.InsertItem(parent, insertafter, item['label'])
            elif appendafter:
                node = self.AppendItem(parent, item['label'])
            else:
                node = self.PrependItem(parent, item['label'])
            self.SetItemData(node, item['data'])
            self.SetItemImage(node, item['icon_normal'])
            self.SetItemImage(node, item['icon_selected'], wx.TreeItemIcon_Selected)
            self.SetItemImage(node, item['icon_expanded'], wx.TreeItemIcon_Expanded)
            self.SetItemImage(node, item['icon_selectedexpanded'], wx.TreeItemIcon_SelectedExpanded)

            newitems.append(node)
            if 'children' in item:
                self.InsertItemsFromList(item['children'], node, appendafter=True)
        return newitems


class ESPFolders(MyTreeCtrl):

    def __init__(self, parent, main_frame):
        self.main_frame = main_frame
        MyTreeCtrl.__init__(
            self,
            parent
        )

        self.root = self.AddRoot(".")
        self.SetItemData(self.root, "")
        self.SetItemImage(self.root, self.fldridx)
        self.SetItemImage(self.root, self.fldropenidx, wx.TreeItemIcon_Expanded)
        self.AddChildren(self.root)

        self.Expand(self.root)

    def OnItemCopyEvent(self, evt):
        pass

    def OnItemCutEvent(self, evt):
        pass

    def OnItemPasteEvent(self, evt):
        pass

    def OnItemDeleteEvent(self, evt):
        pass

    def AddChildren(self, tree_item):
        path = self.GetItemData(tree_item)
        child_item, cookie = self.GetFirstChild(tree_item)
        child_paths = {}

        while child_item.IsOk():
            child_path = self.GetItemData(child_item)
            child_paths[child_path] = child_item
            child_item, cookie = self.GetNextChild(tree_item, cookie)

        contents = self.GetParent().GetDirContent(path)
        folders = []
        files = []
        for item in contents:
            if item.endswith('<dir>'):
                name, timestamp = item.replace('<dir>', '').split('*')
                dir_path = os.path.join(path, name)
                folders += [[name, timestamp, '', dir_path]]

                if dir_path in child_paths:
                    if name != self.GetItemText(child_paths[dir_path]):
                        self.SetItemText(child_paths[dir_path], name)
                    continue

                child = self.AppendItem(tree_item, name)
                self.SetItemData(child, dir_path)
                self.SetItemImage(child, self.fldridx)
                self.SetItemImage(child, self.fldropenidx, wx.TreeItemIcon_Expanded)

                child_contents = self.GetParent().GetDirContent(dir_path)
                for child_item in child_contents:
                    if child_item.endswith('<dir>'):
                        self.SetItemHasChildren(child)
                        break
                else:
                    self.SetItemHasChildren(child, False)

            else:
                name, timestamp, size = item.split('*')
                file_path = os.path.join(path, name)
                files += [[name, timestamp, size, file_path]]

        return folders + files

    def RenameItem(self, src, dst):
        def iter_tree(parent):
            child, cookie = self.GetFirstChild(parent)
            while child.IsOk():
                path = self.GetItemData(child)
                if path == src:
                    name = os.path.split(dst)[1]
                    self.SetItemText(child, name)
                    self.SetItemData(child, dst)
                    self.Refresh()
                    self.Update()
                    return

                if self.ItemHasChildren(child):
                    iter_tree(child)

                child, cookie = self.GetNextChild(parent, cookie)

        iter_tree(self.GetRootItem())

    def DeleteDirTree(self, tree_item):
        path = self.GetItemData(tree_item)
        self.GetParent().DeleteDirTree(path)
        self.Delete(tree_item)

    def ReadFile(self, tree_item):
        path = self.GetItemData(tree_item)
        return self.GetParent().ReadFile(path)

    def WriteFile(self, tree_item, path, data):
        dst_path = self.GetItemData(tree_item)
        path = os.path.join(dst_path, path)

        self.GetParent().WriteFile(path, data)

    def WriteDirTree(self, tree_item, files):
        dst_path = self.GetItemData(tree_item)
        self.GetParent().WriteDirTree(dst_path, files)

    def ReadDirTree(self, tree_item):
        parent_path = self.GetItemData(tree_item)
        dir_tree = self.GetParent().ReadDirTree(parent_path)
        return dir_tree

    def DeleteFile(self, tree_item):
        path = self.GetItemData(tree_item)
        self.GetParent().DeleteFile(path)
        self.RemoveChild(tree_item)

    def OnEndLabelEditEvent(self, evt):
        """
        Handles wx.EVT_TREE_END_LABEL_EDIT
        """
        if evt.IsEditCancelled():
            return

        child_item = evt.GetItem()
        new_label = evt.GetLabel()
        src = self.GetItemData(child_item)
        dst, old_label = os.path.split(src)

        if new_label == old_label:
            return

        dst = os.path.join(dst, new_label)
        if self.GetParent().Rename(src, dst):
            self.SetItemData(child_item, dst)
            self.GetParent().list_ctrl.RenameItem(src, dst)

        evt.Skip()


class LocalFolders(MyTreeCtrl):

    def __init__(self, parent, main_frame):
        self.main_frame = main_frame
        MyTreeCtrl.__init__(self, parent)

        self.dropTarget = DropTarget(self)
        self.SetDropTarget(self.dropTarget)

        self.root = self.AddRoot("C:\\")
        self.SetItemData(self.root, "C:\\")
        self.SetItemImage(self.root, self.fldridx)
        self.SetItemImage(self.root, self.fldropenidx, wx.TreeItemIcon_Expanded)
        self.AddChildren(self.root)

        self.Expand(self.root)

    def OnItemCopyEvent(self, evt):
        pass

    def OnItemCutEvent(self, evt):
        pass

    def OnItemPasteEvent(self, evt):
        pass

    def OnItemDeleteEvent(self, evt):
        pass

    def AddChildren(self, tree_item):
        path = self.GetItemData(tree_item)
        child_item, cookie = self.GetFirstChild(tree_item)
        child_paths = {}

        while child_item.IsOk():
            child_path = self.GetItemData(child_item)
            child_paths[child_path] = child_item
            child_item, cookie = self.GetNextChild(tree_item, cookie)

        files = []
        folders = []

        for name in os.listdir(path):
            f_path = os.path.join(path, name)
            stats = os.stat(f_path)
            timestamp = time.strftime("%m/%d/%Y %I:%M %p", time.localtime(stats.st_mtime))

            if os.path.isdir(f_path):
                folders += [[name, timestamp, '', f_path]]
                if f_path in child_paths:
                    if name != self.GetItemText(child_paths[f_path]):
                        self.SetItemText(child_paths[f_path], name)
                    continue

                child = self.AppendItem(tree_item, name)
                self.SetItemData(child, f_path)
                self.SetItemImage(child, self.fldridx)
                self.SetItemImage(child, self.fldropenidx, wx.TreeItemIcon_Expanded)

                try:
                    for child_path in os.listdir(f_path):
                        child_path = os.path.join(f_path, child_path)
                        if os.path.isdir(child_path):
                            self.SetItemHasChildren(child)
                            break
                    else:
                        self.SetItemHasChildren(child, False)
                except OSError:
                    self.SetItemHasChildren(child, False)

            else:
                size = str(stats.st_size)
                files += [[name, timestamp, size, f_path]]

        return folders + files

    def WriteDirTree(self, tree_item, files):
        dst_path = self.GetItemData(tree_item)
        for path in sorted(list(files.keys())):
            data = files[path]

            path, file_name = os.path.split(path)
            path = os.path.join(dst_path, path)

            if not os.path.exists(path):
                os.makedirs(path)

            if data is None:
                continue

            path = os.path.join(path, file_name)
            with open(path, 'wb') as f:
                f.write(data)

    def ReadDirTree(self, tree_item):
        res = {}
        parent_path = self.GetItemData(tree_item)

        def iter_children(parent):
            p_path = self.GetItemData(parent)
            res[p_path] = None

            child, cookie = self.GetFirstChild(parent)
            while child.IsOk():
                if self.ItemHasChildren(child):
                    iter_children(child)
                else:
                    path = self.GetItemData(child)
                    with open(path, 'rb') as f:
                        res[path.replace(parent_path, '')[1:]] = f.read()

                child, cookie = self.GetNextChild(parent, cookie)

        iter_children(tree_item)
        return res

    def DeleteFile(self, tree_item):
        path = self.GetItemData(tree_item)
        send2trash.send2trash(path)
        self.Delete(tree_item)

    def DeleteDirTree(self, tree_item):
        path = self.GetItemData(tree_item)
        send2trash.send2trash(path)
        self.Delete(tree_item)

    def OnEndLabelEditEvent(self, evt):
        """
        Handles wx.EVT_TREE_END_LABEL_EDIT
        """
        child_item = evt.GetItem()
        new_label = evt.GetLabel()
        parent_item = self.GetItemParent(child_item)
        parent_path = self.GetItemData(parent_item)
        child_path = self.GetItemData(child_item)
        new_path = os.path.join(parent_path, new_label)

        if not evt.IsEditCancelled() and child_path != new_path:
            os.rename(child_path, new_path)
            self.SetItemData(child_item, new_path)

        evt.Skip()
