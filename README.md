# esp32_file_manager
Filemanager and terminal for an ESP32 that is running MicroPython.


This is a work in progress.

When finished drag and drop ability to transfer files to and from the ESP32
running MicroPython will be possible. There is also a REPL terminal  that can be
used at the same time. It does not disconnect and reconnect to the ESP when you 
want to move files and then key something into the terminal.


you may or may not have to supply the com port, it depends on the UART that is used
on the ESP32, If it does not work without supplying a port if you provide me with the 
VID and the PID for your ESP32 I can add the auto detection feature pretty easily.


I will be expanding this so it will be able to support connecting to more then one 
ESP32 at the same time, I need to get the drag and drop portions of the code ironed out
before I do this.

I still have to write a setup script for the installation end of things
There are a couple of requird libraries.

***Requirements***

* wxPython 4.1.1
* pySerial
* send2trash


***Features***

* drag and drop copy
* right click drag and drop with menu to move or copy
* move/copy files and folders from a local disk to the ESP32
* move/copy files and folders from the ESP32 to a local disk
* move/copy files and folders on the ESP32
* file/folder renaming
* delete files/folders
* preview window for images and text based files
* use the terminal and the file manager without ESP32 reboots
* local file/folder deletion goes to the recycle bin


here is what you will need to do to get it running.


    import esp32_file_manager
    
    frame = esp32_file_manager.Frame('COM11', 115200)
    frame.Show()
    esp32_file_manager.app.MainLoop()    