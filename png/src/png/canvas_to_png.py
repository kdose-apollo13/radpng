import tkinter as tk

from png.encoder import encode_rgba

class PixelDrawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter Pure Stdlib Pixel Drawing")

        self.width = 400
        self.height = 300

        # Create a PhotoImage (our pixel buffer)
        self.photo = tk.PhotoImage(width=self.width, height=self.height)
        
        # Start with a transparent canvas
        self.clear()

        # Canvas to display it
        # Note: We give the canvas a checkered gray pattern via CSS or standard style 
        # so you can visually see the transparency of your canvas!
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, 
                               bg="#e0e0e0", highlightthickness=0)
        self.canvas_image = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.canvas.pack()

        # Mouse state
        self.last_x = None
        self.last_y = None
        self.drawing = False

        # Bind events
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

        # Controls
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=8)
        
        tk.Button(btn_frame, text="Clear", command=self.clear).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Print Pixel Grid", command=self.get_pixels).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Save PNG", command=self.save_png).pack(side="left", padx=5)

    def clear(self):
        """Fills the canvas with transparent pixels."""
        # This natively and instantly wipes the entire PhotoImage to fully transparent
        self.photo.blank()

    def start_draw(self, event):
        self.last_x = event.x
        self.last_y = event.y
        self.drawing = True
        self.set_pixel(event.x, event.y, "#000000")

    def stop_draw(self, event):
        self.drawing = False
        self.last_x = None
        self.last_y = None

    def draw(self, event):
        if not self.drawing:
            return
        
        x1, y1 = self.last_x, self.last_y
        x2, y2 = event.x, event.y

        self.draw_line_bresenham(x1, y1, x2, y2, "#000000")

        self.last_x = x2
        self.last_y = y2

    def set_pixel(self, x, y, color="#000000"):
        """Set a single pixel safely"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.photo.put(color, (x, y))

    def draw_line_bresenham(self, x1, y1, x2, y2, color):
        """Bresenham's line algorithm"""
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy

        while True:
            self.set_pixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

    def get_pixels(self):
        """Return 2D list: pixels[y][x] = (r, g, b, a)"""
        pixels = []
        print(f"Extracting {self.width}×{self.height} pixel grid...")
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # 1. Get the base RGB values
                color_data = self.photo.get(x, y)
                
                if isinstance(color_data, tuple):
                    r, g, b = color_data
                else:
                    r, g, b = map(int, color_data.split())
                
                # 2. Get the Alpha channel natively
                # transparency_get() returns True if the pixel is completely transparent
                is_transparent = self.photo.transparency_get(x, y)
                
                # If transparent, Alpha is 0. If solid, Alpha is 255.
                a = 0 if is_transparent else 255
                
                row.append((r, g, b, a))
            pixels.append(row)
        
        print("Top-left 5x5 preview:")
        for y in range(min(5, self.height)):
            print(pixels[y][:5])
        
        return pixels


    def save_png(self, filename="canvas_output.png"):
        """Saves the exact pixel buffer directly into a valid PNG file using pure-python encoder (no tkinter PNG writer)."""
        try:
            # use the radical pure stdlib encoder for symmetry demo (4-tuples -> png bytes)
            pixels = self.get_pixels()
            png_bytes = encode_rgba(pixels)
            with open(filename, 'wb') as f:
                f.write(png_bytes)
            print(f'Successfully saved pure-png to {filename}')
            # one-liner roundtrip example: back = decode_rgba(encode_rgba(self.get_pixels()))
        except Exception as e:
            print(f'Error saving image: {e}')


if __name__ == "__main__":
    root = tk.Tk()
    app = PixelDrawApp(root)
    root.mainloop()
