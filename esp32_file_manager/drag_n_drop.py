import wx
import time

from . import HITTEST_FLAGS


class DropSource(wx.DropSource):
    """
    This class represents a source for a drag and drop operation of the
    TreeCtrl.
    """
    def __init__(self, win, text):
        wx.DropSource.__init__(self, win)
        # create our own data format and use it in a
        # custom data object
        customData = wx.CustomDataObject("DragItem")
        customData.SetData(text)

        # Now make a data object for the text and also a composite
        # data object holding both of the others.
        textData = wx.TextDataObject(text.decode("UTF-8"))

        data = wx.DataObjectComposite()
        data.Add(textData)
        data.Add(customData)

        # We need to hold a reference to our data object, instead it could
        # be garbage collected
        self.data = data

        # And finally, create the drop source and begin the drag
        # and drop operation
        self.SetData(data)


class DropTarget(wx.DropTarget):
    """
    This class represents a target for a drag and drop operation of the
    TreeCtrl.
    """
    def __init__(self, treeCtrl):
        wx.DropTarget.__init__(self)
        self.treeCtrl = treeCtrl

        # specify the type of data we will accept
        textData = wx.TextDataObject()
        self.customData = wx.CustomDataObject(wx.DataFormat("DragItem"))
        self.customData.SetData(b"")
        compositeData = wx.DataObjectComposite()
        compositeData.Add(textData)
        compositeData.Add(self.customData)
        self.SetDataObject(compositeData)
        self.lastHighlighted = None
        self.isExternalDrag = True
        self.left_drag = False
        self.source = None
        self.lastDropTime = time.time()
        self.lastTargetItemId = None
        timerId = wx.NewIdRef()
        self.autoScrollTimer = wx.Timer(self.treeCtrl, timerId)
        self.treeCtrl.Bind(wx.EVT_TIMER, self.OnDragTimerEvent, id=timerId)

    def OnData(self, x, y, drag_result):
        if self.lastTargetItemId is not None:
            drag_source = self.treeCtrl.GetParent().drag_source
            tree = self.treeCtrl
            target = self.lastTargetItemId

            def MoveHere(_):
                if drag_source == tree:
                    save = tree.SaveItemsToList(tree.drop_target.source)

                    tree_item = tree.drop_target.source

                    if tree.ItemHasChildren(tree_item):
                        tree.DeleteDirTree(tree_item)
                    else:
                        tree.DeleteFile(tree_item)

                    tree.Delete(tree.drop_target.source)
                else:
                    save = drag_source.SaveItemsToList(drag_source.drop_target.source)
                    drag_source.Delete(drag_source.drop_target.source)

                newitems = tree.InsertItemsFromList(save, target)
                for item in newitems:
                    tree.SelectItem(item)

            def CopyHere(_):
                if drag_source == tree:
                    save = tree.SaveItemsToList(tree.drop_target.source)
                else:
                    save = drag_source.SaveItemsToList(drag_source.drop_target.source)

                newitems = tree.InsertItemsFromList(save, target)
                for item in newitems:
                    tree.SelectItem(item)

            if drag_source == tree:
                left_drag = tree.drop_target.left_drag
            else:
                if not tree.ItemHasChildren(target):
                    target = tree.GetItemParent(target)

                if not tree.IsExpanded(target):
                    tree.Expand(target)

                left_drag = drag_source.drop_target.left_drag

            if left_drag:
                CopyHere(None)
            else:
                menu = wx.Menu()
                menu.Append(101, "Move", "")
                menu.Append(wx.ID_COPY, "Copy", "")
                menu.UpdateUI()
                menu.Bind(wx.EVT_MENU, MoveHere, id=101)
                menu.Bind(wx.EVT_MENU, CopyHere, id=wx.ID_COPY)
                tree.PopupMenu(menu, x, y)

        return drag_result

    def OnDragOver(self, x, y, dummyDragResult):
        """
        Called when the mouse is being dragged over the drop target.
        """
        tree = self.treeCtrl

        if tree.GetParent().drag_source is None:
            return wx.DragNone

        # remove the last drop highlight if any
        if self.lastHighlighted is not None:
            tree.SetItemDropHighlight(self.lastHighlighted, False)
            self.lastHighlighted = None

        dstItemId, flags = tree.HitTest((x, y))

        if not (flags & HITTEST_FLAGS):
            return wx.DragNone

        if not tree.ItemHasChildren(dstItemId):
            dstItemId = tree.GetItemParent(dstItemId)

        # expand a container, if the mouse is hold over it for some time
        if dstItemId == self.lastTargetItemId:
            if self.lastDropTime + 0.6 < time.time():
                if not tree.IsExpanded(dstItemId):
                    tree.Expand(dstItemId)

            self.lastHighlighted = dstItemId
            tree.SetItemDropHighlight(self.lastHighlighted, True)

        else:
            self.lastDropTime = time.time()
            self.lastTargetItemId = dstItemId
            self.lastHighlighted = dstItemId
            tree.SetItemDropHighlight(self.lastHighlighted, True)

        return wx.DragMove

    def OnDragTimerEvent(self, _):
        """
        Handles wx.EVT_TIMER, while a drag operation is in progress. It is
        responsible for the automatic scrolling if the mouse gets on the
        upper or lower bounds of the control.
        """
        tree = self.treeCtrl
        x, y = wx.GetMousePosition()
        treeRect = tree.GetScreenRect()
        if treeRect.x <= x <= treeRect.GetRight():
            if y < treeRect.y + 20:
                tree.ScrollLines(-1)
            elif y > treeRect.GetBottom() - 20:
                tree.ScrollLines(1)

    def OnEnter(self, dummyX, dummyY, dragResult):
        """
        Called when the mouse enters the drop target.
        """
        self.autoScrollTimer.Start(50)
        return dragResult

    def OnLeave(self):
        """
        Called when the mouse leaves the drop target.
        """
        self.autoScrollTimer.Stop()
