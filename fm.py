'''
    icon from: https://www.flaticon.com/free-icons/eye-tracking
    pyinstaller -F -w -i res\eye.png --add-data res\eye.png:res --clean fm.py
'''

import wx, ctypes, win32con, win32gui, screeninfo, time, pynput, threading, \
pystray, sys, os
from PIL import Image


class ShapedFrame(wx.Frame):
    def __init__(self, initx, inity, initw, inith):
        wx.Frame.__init__(self, None, -1, "Focus Mode",
                style = wx.FRAME_SHAPED | wx.NO_BORDER)

        self.opacity = 128              # Opacity of darkness (0-255)
        self.keep_highlighted = 0       # 0 = 1 window
        self.cooldown = 1               # Seconds between fades
        self.fade_time = 0.003          # Seconds for fade in/out transition
        self.faded = False              # Is faded out

        self.window_num_select = {0: True, 1: False, 2: False, 3: False, -1: False}
        self.opacity_select = {'10%': False, '15%': False, '20%': False, '25%': False, '30%': False, 
                               '35%': False, '40%': False, '45%': False, '50%': True, '55%': False,
                               '60%': False, '65%': False, '70%': False, '75%': False, '80%': False,
                               '85%': False, '90%': False, '95%': False,}

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


    def OnEraseBackground(self, evt=None):
        pass


    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 0,0, True)
    

    def fade_out(self):
        for i in range(self.opacity, 0, -1):
            self.SetTransparent(i)
            time.sleep(self.fade_time)
        self.faded = False


    def fade_in(self):
        for i in range(self.opacity):
            self.SetTransparent(i)
            time.sleep(self.fade_time)
        self.faded = True

    
    def fade_out_in(self, op):
        self.fade_out()
        self.SetTransparent(op)
        time.sleep(self.cooldown)
        self.fade_in()


    def enumHandler(self, hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd) and \
        win32gui.GetWindowText(hwnd) != '' \
        and win32gui.GetWindowText(hwnd) != 'Focus Mode':
            self.top.append(hwnd)


    def global_click(self, x, y, z, a):
        if not a:
            # Mouse click release (sets top window) and clicked a different window
            fore = win32gui.GetForegroundWindow()           # Get top window
            win32gui.EnumWindows(self.enumHandler, None)    # Fill self.top with PIDs of open windows
            
            if self.keep_highlighted != -1:         # If number is selected
                win32gui.SetWindowPos(self.hwnd, self.top[self.keep_highlighted], 0,0,0,0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                
            if win32gui.GetWindowText(fore) == 'Program Manager':  # Clicked desktop
                self.t = threading.Thread(target=self.fade_out)
                if not self.t.is_alive():
                        self.t.start()
            elif not self.faded:
                win32gui.SetWindowPos(self.hwnd, fore, 0,0,0,0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                self.t = threading.Thread(target=self.fade_in)
                if not self.t.is_alive():
                        self.t.start()
            
            # Check window order
            print([win32gui.GetWindowText(t) for t in self.top])
            self.top = []


    def set_highlight_num(self, x, y):
        for k in self.window_num_select:
            self.window_num_select[k] = False

        if y.text == 'None':
            self.keep_highlighted = -1
        else:
            self.keep_highlighted = int(y.text) - 1
            win32gui.SetWindowPos(self.hwnd, win32gui.GetForegroundWindow(), 0,0,0,0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
        self.window_num_select[self.keep_highlighted] = True
    

    def set_opacity(self, obj, op):
        for k in self.opacity_select:
            self.opacity_select[k] = False
        
        num = int(op.text[:-1])
        self.opacity_select[op.text] = True
        self.fade_out()
        self.opacity = int((num / 100) * 255)
        time.sleep(self.cooldown)
        self.fade_in()
            
        

def quit(tray):
    sf.fade_out()
    sf.Close()
    tray.stop()
    

if __name__ == '__main__':
    app = wx.App()

    if hasattr(sys, '_MEIPASS'):
        os.chdir(sys._MEIPASS)

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

    ico = Image.open('res/eye.png')

    opacity_menu = []
    for i in sf.opacity_select:
        opacity_menu.append(pystray.MenuItem(i, sf.set_opacity, radio=True, checked=lambda item, key=i: sf.opacity_select[key]))

    pystray.Icon('FocusMode', icon=ico, menu=pystray.Menu(
        pystray.MenuItem('Opacity', pystray.Menu(
            *opacity_menu
        )),
        pystray.MenuItem('# of windows', pystray.Menu(
            pystray.MenuItem('1', sf.set_highlight_num, radio=True, checked=lambda item: sf.window_num_select[0]),
            pystray.MenuItem('2', sf.set_highlight_num, radio=True, checked=lambda item: sf.window_num_select[1]),
            pystray.MenuItem('3', sf.set_highlight_num, radio=True, checked=lambda item: sf.window_num_select[2]),
            pystray.MenuItem('4', sf.set_highlight_num, radio=True, checked=lambda item: sf.window_num_select[3]),
            pystray.MenuItem('None', sf.set_highlight_num, radio=True, checked=lambda item: sf.window_num_select[-1]),
        )),
        pystray.MenuItem('Quit', quit)
        )).run_detached()
    
    
    app.MainLoop()
    l.stop()
    
    
    

