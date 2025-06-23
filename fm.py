'''
    TODO make a background frame, then a second frame that fades in when clicking a new window
    icon from: https://www.flaticon.com/free-icons/eye-tracking
'''

import wx, ctypes, win32con, win32gui, sys, screeninfo, time, pynput, threading, \
pystray
from PIL import Image


class ShapedFrame(wx.Frame):
    def __init__(self, initx, inity, initw, inith):
        wx.Frame.__init__(self, None, -1, "Focus Mode",
                style = wx.FRAME_SHAPED | wx.NO_BORDER)

        self.opacity = 100              # Opacity of darkness (0-255)
        self.keep_highlighted = 0       # 0 = 1 window
        self.cooldown = 0               # Seconds between fades
        self.fade_time = 0.003          # Seconds for fade in/out transition

        # Make window clicks go through and not appear in taskbar
        self.hwnd = self.GetHandle()
        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOOLWINDOW
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style)

        ctypes.windll.user32.ShowWindow(self.hwnd, 0)
        
        # Create a black image that mathces the size of the resoltion
        image = wx.Image(initw, inith)
        # Create bitmap from black image
        self.bmp = wx.Bitmap(image)
        # Set the frame size equal to resolution
        self.SetClientSize((initw, inith))
        # Draw bitmap on screen
        dc = wx.ClientDC(self)
        dc.DrawBitmap(self.bmp, 0, 0)
        # Move to top-left most corner (multi-monitor)
        self.Move((initx, inity))
        # Initialize list of windows clicked on
        self.top = [win32gui.GetForegroundWindow(),]
        
        win32gui.SetWindowPos(self.hwnd, self.top[0], 0,0,0,0,
                                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
        
        threading.Thread(target=self.fade_in, daemon=True).start()

        #self.SetWindowShape()
        #self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        #self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        #self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        #self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        #self.Bind(wx.EVT_RIGHT_UP, self.OnExit)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        #self.Bind(wx.EVT_WINDOW_CREATE, self.SetWindowShape)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)


    def OnEraseBackground(self,evt=None):
        pass


    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 0,0, True)
    

    def get_name(self, w):
        length = ctypes.windll.user32.GetWindowTextLengthW(w)
        if length == 0:
            return ""
        buffer = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(w, buffer, length + 1)
        return buffer.value
    

    def fade_out(self):
        for i in range(self.opacity, 0, -1):
            self.SetTransparent(i)
            time.sleep(self.fade_time)


    def fade_in(self):
        for i in range(self.opacity):
            self.SetTransparent(i)
            time.sleep(self.fade_time)

    
    def switch(self):
        self.fade_out()
        time.sleep(self.cooldown)
        self.fade_in()
        

    def global_click(self, x, y, z, a):
        if not a:
            # Mouse click release (sets top window) and clicked a different window
            if self.keep_highlighted != -1:
                fore = win32gui.GetForegroundWindow()
                if fore not in self.top:
                    if len(self.top) > self.keep_highlighted:
                        self.top.pop(0)
                    self.top.append(fore)
                    print(self.top[-1])
                    if self.top[-1] == 132814:  # Clicked desktop
                        self.top.clear()
                        self.fade_out()
                    else:
                        self.t = threading.Thread(target=self.switch)
                        if not self.t.is_alive():
                            win32gui.SetWindowPos(self.hwnd, self.top[-self.keep_highlighted], 0,0,0,0,
                                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                            self.t.start()
            #print(self.top)

    def quit(self):
        self.t.join()
        self.Close()


    def set_highlight_num(self, x, y):
        if y.text == 'None':
            self.keep_highlighted = -1
        else:
            self.keep_highlighted = int(y.text)
        

def quit(tray):
    sf.quit()
    tray.stop()
    

if __name__ == '__main__':
    app = wx.App()

    leastx = 0
    leasty = 0

    # Get top left corner of monitors
    for m in screeninfo.get_monitors():
        if m.x < leastx:
            leastx = m.x
        if m.y < leasty:
            leasty = m.y

    # Get total resolution of all monitors together
    u32 = ctypes.windll.user32
    screensize = u32.GetSystemMetrics(78), u32.GetSystemMetrics(79)
    
    sf = ShapedFrame(leastx, leasty, screensize[0], screensize[1])
    sf.Show()

    l = pynput.mouse.Listener(on_click=sf.global_click)
    l.start()

    ico = Image.open('eye.png')
    pystray.Icon('FocusMode', icon=ico, menu=pystray.Menu(
        pystray.MenuItem('# of windows', pystray.Menu(
            pystray.MenuItem('1', sf.set_highlight_num, radio=True),
            pystray.MenuItem('2', sf.set_highlight_num, radio=True),
            pystray.MenuItem('3', sf.set_highlight_num, radio=True),
            pystray.MenuItem('4', sf.set_highlight_num, radio=True),
            pystray.MenuItem('None', sf.set_highlight_num, radio=True),
            )),
        pystray.MenuItem('Quit', quit)
        )).run_detached()
    
    
    app.MainLoop()
    l.stop()
    
    #sys.exit(0)
    
