import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import numpy as np
import cv2
import os

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Lightroom Matcher Pro")
        self.root.geometry("900x700")
        self.root.configure(bg='#1e1e1e')
        self.ref_img = None
        self.src_img = None
        
        tk.Label(root, text="Lightroom Style Matcher", fg="#4db8ff", bg="#1e1e1e", font=("Segoe UI", 24, "bold")).pack(pady=20)
        frame = tk.Frame(root, bg="#1e1e1e")
        frame.pack(pady=10)
        
        self.ref_box = tk.Label(frame, text="Ref Image (Style to Match)", bg="#2d2d2d", fg="#888", width=40, height=15, relief="flat")
        self.ref_box.grid(row=0, column=0, padx=20)
        tk.Button(frame, text="Select Reference", command=self.set_ref, bg="#444", fg="white", relief="flat", padx=10).grid(row=1, column=0, pady=10)
        
        self.src_box = tk.Label(frame, text="Source Image (To be Edited)", bg="#2d2d2d", fg="#888", width=40, height=15, relief="flat")
        self.src_box.grid(row=0, column=1, padx=20)
        tk.Button(frame, text="Select Source", command=self.set_src, bg="#444", fg="white", relief="flat", padx=10).grid(row=1, column=1, pady=10)
        
        tk.Button(root, text="GENERATE .XMP PRESET", command=self.run, bg="#28a745", fg="white", font=("Segoe UI", 14, "bold"), relief="flat", padx=30, pady=10).pack(pady=30)
        
        self.log = scrolledtext.ScrolledText(root, height=8, bg="#121212", fg="#00ff00", font=("Consolas", 10))
        self.log.pack(fill="x", padx=40)
        self.log.insert("end", "System Ready.")

    def set_img(self, lbl):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.tif *.tiff")])
        if path:
            try:
                img = Image.open(path)
                img.thumbnail((300, 250))
                ph = ImageTk.PhotoImage(img)
                lbl.config(image=ph, text="")
                lbl.image = ph
                cv_img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
                return cv_img
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
        return None

    def set_ref(self): self.ref_img = self.set_img(self.ref_box)
    def set_src(self): self.src_img = self.set_img(self.src_box)

    def calculate_metrics(self):
        r_lab = cv2.cvtColor(self.ref_img, cv2.COLOR_BGR2LAB).astype(np.float32)
        s_lab = cv2.cvtColor(self.src_img, cv2.COLOR_BGR2LAB).astype(np.float32)
        exp = (np.mean(r_lab[:,:,0]) - np.mean(s_lab[:,:,0])) / 50.0
        r_std = np.std(r_lab[:,:,0])
        s_std = np.std(s_lab[:,:,0])
        contrast = int((r_std / (s_std + 1e-6) - 1.0) * 100)
        contrast = max(-100, min(100, contrast))
        temp = int((np.mean(r_lab[:,:,2]) - np.mean(s_lab[:,:,2])) * 0.5)
        tint = int((np.mean(r_lab[:,:,1]) - np.mean(s_lab[:,:,1])) * 0.5)
        return {"Exposure2012": round(exp, 2), "Contrast2012": contrast, "Temperature": temp, "Tint": tint}

    def run(self):
        if self.ref_img is None or self.src_img is None:
            messagebox.showwarning("Warning", "Select both images.")
            return
        try:
            m = self.calculate_metrics()
            xmp_content = f"""<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 7.0-c000 79.daa7c53, 2021/02/18-15:30:12        ">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:crs="http://ns.adobe.com/camera-raw-settings/1.0/"
   crs:PresetType="Normal"
   crs:Cluster=""
   crs:UUID="{os.urandom(16).hex().upper()}"
   crs:SupportsAmount="True"
   crs:SupportsColor="True"
   crs:SupportsMonochrome="True"
   crs:SupportsHighDynamicRange="True"
   crs:SupportsNormalDynamicRange="True"
   crs:SupportsSceneReferred="True"
   crs:SupportsOutputReferred="True"
   crs:CameraConfig="Camera v2"
   crs:HasSettings="True"
   crs:Exposure2012="{m["Exposure2012"]}"
   crs:Contrast2012="{m["Contrast2012"]}"
   crs:Highlights2012="0"
   crs:Shadows2012="0"
   crs:Whites2012="0"
   crs:Blacks2012="0"
   crs:Temperature="{m["Temperature"]}"
   crs:Tint="{m["Tint"]}"
   crs:HasCrop="False"
   crs:AlreadyApplied="True">
   <crs:Name>
    <rdf:Alt>
     <rdf:li xml:lang="x-default">Matched Style</rdf:li>
    </rdf:Alt>
   </crs:Name>
   <crs:Group>
    <rdf:Alt>
     <rdf:li xml:lang="x-default">User Presets</rdf:li>
    </rdf:Alt>
   </crs:Group>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>"""
            path = filedialog.asksaveasfilename(defaultextension=".xmp", filetypes=[("XMP files", "*.xmp")])
            if path:
                with open(path, "wb") as f:
                    f.write(b'\\xef\\xbb\\xbf') # UTF-8 BOM
                    f.write(b'<?xpacket begin="\\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>\
')
                    f.write(xmp_content.encode("utf-8"))
                    f.write(b'\
<?xpacket end="w"?>')
                self.log.insert("end", f"Saved: {path}")
                messagebox.showinfo("Success", "Preset saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
