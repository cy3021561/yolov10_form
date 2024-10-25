import tkinter as tk
from enum import Enum
import platform

class OverlayState(Enum):
    RUNNING = "running"
    READY = "ready"
    OFF = "off"

class ScreenOverlay:
    def __init__(self, border_width=3):
        self.border_width = border_width
        self.state = OverlayState.OFF
        self.running = True
        
        # Initialize GUI
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window
        
        # Create overlay windows for each edge
        self.edges = []
        for _ in range(4):
            edge = tk.Toplevel(self.root)
            edge.overrideredirect(True)
            edge.attributes('-topmost', True)
            edge.attributes('-alpha', 0.7)
            edge.withdraw()
            self.edges.append(edge)
            
        # Create status window with black background
        self.status_window = tk.Toplevel(self.root)
        self.status_window.title("")  # Remove the "tk" title
        self.status_window.overrideredirect(True)
        self.status_window.attributes('-topmost', True)
        self.status_window.attributes('-alpha', 0.9)
        
        # Make the status window click-through
        if platform.system().lower() == 'darwin':  # macOS
            self.status_window.attributes('-transparent', True)
        else:  # Windows
            self.status_window.attributes('-transparentcolor', 'black')
        
        # Create a frame with black background for the status
        self.status_frame = tk.Frame(
            self.status_window,
            background='black',
            padx=10,
            pady=5
        )
        self.status_frame.pack(expand=True, fill='both')
        
        # Configure status label with explicit size and styling
        self.status_label = tk.Label(
            self.status_frame,
            text="Initializing...",
            width=40,
            height=2,
            background='black',
            foreground='white',
            font=('MS Sans Serif', 15, 'bold'),
            wraplength=300,
            justify='center'
        )
        self.status_label.pack(expand=True, fill='both')
        
        # Initialize status window position
        self.status_window.withdraw()
        self._position_overlays()
        
        # Start the topmost maintenance
        self._maintain_topmost()
        
    def _maintain_topmost(self):
        """Ensure windows stay on top using the main thread"""
        if self.running and self.state != OverlayState.OFF:
            try:
                self.status_window.lift()
                self.status_window.attributes('-topmost', True)
                for edge in self.edges:
                    edge.lift()
                    edge.attributes('-topmost', True)
            except tk.TclError:
                pass
        
        if self.running:
            self.root.after(5, self._maintain_topmost)
        
    def _get_screen_dimensions(self):
        """Get screen dimensions accounting for DPI scaling"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        return screen_width, screen_height
        
    def _position_overlays(self):
        """Position the border overlays and status window"""
        width, height = self._get_screen_dimensions()
        
        # Position edges (top, right, bottom, left)
        edge_coords = [
            # Top: full width
            (0, 0, width, self.border_width),
            
            # Right: from top border to bottom border
            (width - self.border_width, self.border_width, 
            self.border_width, height - 2 * self.border_width),
            
            # Bottom: full width
            (0, height - self.border_width, width, self.border_width),
            
            # Left: from top border to bottom border
            (0, self.border_width, 
            self.border_width, height - 2 * self.border_width)
        ]
        
        for edge, (x, y, w, h) in zip(self.edges, edge_coords):
            edge.geometry(f"{w}x{h}+{x}+{y}")
            
        # Position status window at bottom-left with fixed size
        status_width = 300
        status_height = 50
        status_x = width - status_width - 40  # 20 pixels from left edge
        status_y = 60  # 40 pixels from bottom
        self.status_window.geometry(f"{status_width}x{status_height}+{status_x}+{status_y}")
            
    def set_state(self, state: OverlayState):
        """Set the overlay state and update colors"""
        self.state = state
        color = {
            OverlayState.RUNNING: '#FF0000',  # Red
            OverlayState.READY: '#00FF00',    # Green
            OverlayState.OFF: None
        }[state]
        
        if state == OverlayState.OFF:
            for edge in self.edges:
                edge.withdraw()
            self.status_window.withdraw()
        else:
            for edge in self.edges:
                edge.configure(bg=color)
                edge.deiconify()
            self.status_window.deiconify()
            self._position_overlays()
            
    def update_status(self, message: str):
        """Update the status message"""
        if not self.running:
            return
            
        try:
            self.status_label.config(text=message)
            self.root.update()  # Force immediate update
        except tk.TclError:
            pass
        
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass

    def start(self):
        """Start the main loop"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Error in mainloop: {e}")
            self.cleanup()


if __name__ == "__main__":
    overlay = ScreenOverlay()
    
    def test_sequence():
        overlay.set_state(OverlayState.RUNNING)
        overlay.update_status("Testing overlay...")
        overlay.root.after(2000, lambda: overlay.update_status("This is a longer message to test the display"))
        overlay.root.after(4000, lambda: overlay.set_state(OverlayState.READY))
        overlay.root.after(4000, lambda: overlay.update_status("Ready!"))
        overlay.root.after(6000, overlay.cleanup)
    
    overlay.root.after(100, test_sequence)
    overlay.start()