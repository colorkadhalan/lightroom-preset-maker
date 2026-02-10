import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import numpy as np
import cv2
from pathlib import Path
from datetime import datetime
import os

class LightroomPresetMaker:
    def __init__(self, root):
        self.root = root
        self.root.title("Lightroom Match Preset Maker")
        self.root.geometry("1000x800")
        self.root.configure(bg='#2b2b2b')
        
        self.reference_image = None
        self.source_image = None
        
        self.setup_ui()
    
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        header = tk.Frame(self.root, bg='#1e1e1e', height=80)
        header.pack(fill=tk.X)
        tk.Label(header, text="Lightroom Match Preset Maker", font=("Segoe UI", 24, "bold"), bg='#1e1e1e', fg='white').pack(pady=20)
        
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        upload_frame = tk.Frame(main_frame, bg='#2b2b2b')
        upload_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.ref_frame = self.create_image_box(upload_frame, "1. Reference (Look to Match)", self.load_reference)
        self.ref_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.src_frame = self.create_image_box(upload_frame, "2. Source (Photo to Style)", self.load_source)
        self.src_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        gen_btn = tk.Button(main_frame, text="GENERATE PRESET", command=self.generate_preset, bg='#107c10', fg='white', font=("Segoe UI", 14, "bold"), relief=tk.FLAT, padx=40, pady=15)
        gen_btn.pack(pady=20)
        
        output_frame = tk.LabelFrame(main_frame, text="Output & Analysis", bg='#3a3a3a', fg='white', font=("Segoe UI", 12, "bold"))
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, bg='#1e1e1e', fg='#d4d4d4', font=("Consolas", 10))
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_image_box(self, parent, title, cmd):
        frame = tk.LabelFrame(parent, text=title, bg='#3a3a3a', fg='white', font=("Segoe UI", 10, "bold"), bd=2)
        label = tk.Label(frame, text="No image selected", bg='#4a4a4a', fg='#999', width=30, height=12)
        label.pack(padx=10, pady=10)
        btn = tk.Button(frame, text="Choose Image", command=lambda: cmd(label), bg='#0078d4', fg='white', font=("Segoe UI", 10, "bold"), relief=tk.FLAT, pady=8)
        btn.pack(pady=10)
        return frame

    def load_image(self, label):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.tiff")])
        if path:
            img = Image.open(path)
            img.thumbnail((300, 250))
            photo = ImageTk.PhotoImage(img)
            label.configure(image=photo, text="")
            label.image = photo
            return cv2.imread(path), path
        return None, None

    def load_reference(self, label):
        self.reference_image, _ = self.load_image(label)
    
    def load_source(self, label):
        self.source_image, _ = self.load_image(label)

    def generate_preset(self):
        if self.reference_image is None or self.source_image is None:
            messagebox.showerror("Error", "Please upload both images!")
            return
            
        adj = self.analyze()
        xmp = self.create_xmp(adj)
        
        save_path = filedialog.asksaveasfilename(defaultextension=".xmp", filetypes=[("XMP Preset", "*.xmp")])
        if save_path:
            with open(save_path, 'w') as f: f.write(xmp)
            self.output_text.insert(tk.END, f"Successfully saved preset to: {save_path}\n")

    def analyze(self):
        ref_lab = cv2.cvtColor(self.reference_image, cv2.COLOR_BGR2LAB)
        src_lab = cv2.cvtColor(self.source_image, cv2.COLOR_BGR2LAB)
        
        # Simple Mean-based Matching
        exp = (np.mean(ref_lab[:,:,0]) - np.mean(src_lab[:,:,0])) / 50.0
        temp = (np.mean(ref_lab[:,:,2]) - np.mean(src_lab[:,:,2])) * 10
        tint = (np.mean(ref_lab[:,:,1]) - np.mean(src_lab[:,:,1])) * 10
        
        return {'Exposure': round(exp, 2), 'Temp': round(temp, 0), 'Tint': round(tint, 0)}

    def create_xmp(self, adj):
        return f"""<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description xmlns:crs="http://ns.adobe.com/camera-raw-settings/1.0/"
   crs:Exposure2012="{adj['Exposure']}"
   crs:Temperature="{adj['Temp']}"
   crs:Tint="{adj['Tint']}"
   crs:HasSettings="True"/>
 </rdf:RDF>
</x:xmpmeta>"""

if __name__ == "__main__":
    root = tk.Tk()
    app = LightroomPresetMaker(root)
    root.mainloop()
