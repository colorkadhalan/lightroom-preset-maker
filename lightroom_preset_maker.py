import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import numpy as np
import cv2

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Lightroom Matcher")
        self.root.geometry("800x600")
        self.root.configure(bg='#222')
        self.ref_img = None
        self.src_img = None
        
        tk.Label(root, text="Lightroom Preset Matcher", fg="white", bg="#222", font=("Arial", 20)).pack(pady=10)
        
        frame = tk.Frame(root, bg="#222")
        frame.pack(pady=10)
        
        self.ref_lbl = tk.Label(frame, text="Ref", bg="#444", width=25, height=10)
        self.ref_lbl.grid(row=0, column=0, padx=10)
        tk.Button(frame, text="Select Reference", command=self.set_ref).grid(row=1, column=0)
        
        self.src_lbl = tk.Label(frame, text="Source", bg="#444", width=25, height=10)
        self.src_lbl.grid(row=0, column=1, padx=10)
        tk.Button(frame, text="Select Source", command=self.set_src).grid(row=1, column=1)
        
        tk.Button(root, text="GENERATE PRESET", command=self.run, bg="green", fg="white", font=("Arial", 12, "bold")).pack(pady=20)
        self.log = scrolledtext.ScrolledText(root, height=5)
        self.log.pack(fill="x", padx=20)

    def set_img(self, lbl):
        path = filedialog.askopenfilename()
        if path:
            img = Image.open(path)
            img.thumbnail((200, 150))
            ph = ImageTk.PhotoImage(img)
            lbl.config(image=ph, text="")
            lbl.image = ph
            return cv2.imread(path)
        return None

    def set_ref(self): self.ref_img = self.set_img(self.ref_lbl)
    def set_src(self): self.src_img = self.set_img(self.src_lbl)

    def run(self):
        if self.ref_img is None or self.src_img is None:
            messagebox.showerror("Error", "Select both images")
            return
        r_lab = cv2.cvtColor(self.ref_img, cv2.COLOR_BGR2LAB)
        s_lab = cv2.cvtColor(self.src_img, cv2.COLOR_BGR2LAB)
        exp = (np.mean(r_lab[:,:,0]) - np.mean(s_lab[:,:,0])) / 50.0
        
        xmp = f'<?xml version="1.0"?><x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description xmlns:crs="http://ns.adobe.com/camera-raw-settings/1.0/" crs:Exposure2012="{round(exp,2)}" crs:HasSettings="True"/></rdf:RDF></x:xmpmeta>'
        
        path = filedialog.asksaveasfilename(defaultextension=".xmp")
        if path:
            with open(path, "w", encoding="utf-8") as f: f.write(xmp)
            self.log.insert("end", f"Saved: {path}\n")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
