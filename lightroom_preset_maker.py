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
        # Convert to LAB color space for analysis
        r_lab = cv2.cvtColor(self.ref_img, cv2.COLOR_BGR2LAB).astype(np.float32)
        s_lab = cv2.cvtColor(self.src_img, cv2.COLOR_BGR2LAB).astype(np.float32)
        
        # Convert to HSV for HSL adjustments
        r_hsv = cv2.cvtColor(self.ref_img, cv2.COLOR_BGR2HSV).astype(np.float32)
        s_hsv = cv2.cvtColor(self.src_img, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Basic exposure and contrast
        exp = (np.mean(r_lab[:,:,0]) - np.mean(s_lab[:,:,0])) / 50.0
        r_std = np.std(r_lab[:,:,0])
        s_std = np.std(s_lab[:,:,0])
        contrast = int((r_std / (s_std + 1e-6) - 1.0) * 100)
        contrast = max(-100, min(100, contrast))
        
        # Temperature and Tint
        temp = int((np.mean(r_lab[:,:,2]) - np.mean(s_lab[:,:,2])) * 0.5)
        tint = int((np.mean(r_lab[:,:,1]) - np.mean(s_lab[:,:,1])) * 0.5)
        
        # Highlights and Shadows (based on percentiles)
        r_highlights = np.percentile(r_lab[:,:,0], 90)
        s_highlights = np.percentile(s_lab[:,:,0], 90)
        highlights = int((r_highlights - s_highlights) / 2.55)
        highlights = max(-100, min(100, highlights))
        
        r_shadows = np.percentile(r_lab[:,:,0], 10)
        s_shadows = np.percentile(s_lab[:,:,0], 10)
        shadows = int((r_shadows - s_shadows) / 2.55)
        shadows = max(-100, min(100, shadows))
        
        # Vibrance and Saturation (from HSV)
        r_sat = np.mean(r_hsv[:,:,1])
        s_sat = np.mean(s_hsv[:,:,1])
        saturation = int((r_sat - s_sat) / 2.55)
        saturation = max(-100, min(100, saturation))
        vibrance = int(saturation * 0.7)  # Vibrance is gentler
        
        # HSL Color Adjustments (analyze per hue range)
        hsl_adjustments = self.calculate_hsl(r_hsv, s_hsv)
        
        # Tone Curve points (simple 3-point curve based on shadows/mids/highlights)
        tone_curve = self.calculate_tone_curve(r_lab, s_lab)
        
        # Color Grading (split toning)
        color_grading = self.calculate_color_grading(r_lab, s_lab)
        
        return {
            "Exposure2012": round(exp, 2),
            "Contrast2012": contrast,
            "Highlights2012": highlights,
            "Shadows2012": shadows,
            "Temperature": temp,
            "Tint": tint,
            "Saturation": saturation,
            "Vibrance": vibrance,
            "HSL": hsl_adjustments,
            "ToneCurve": tone_curve,
            "ColorGrading": color_grading
        }
    
    def calculate_hsl(self, r_hsv, s_hsv):
        """Calculate HSL adjustments for 8 color ranges"""
        hsl = {}
        color_ranges = {
            "Red": (0, 30),
            "Orange": (30, 60),
            "Yellow": (60, 90),
            "Green": (90, 150),
            "Aqua": (150, 180),
            "Blue": (180, 240),
            "Purple": (240, 300),
            "Magenta": (300, 360)
        }
        
        for color, (h_min, h_max) in color_ranges.items():
            # Create mask for this hue range
            mask_r = ((r_hsv[:,:,0] >= h_min) & (r_hsv[:,:,0] < h_max)).astype(float)
            mask_s = ((s_hsv[:,:,0] >= h_min) & (s_hsv[:,:,0] < h_max)).astype(float)
            
            if mask_r.sum() > 0 and mask_s.sum() > 0:
                # Hue shift
                r_hue = np.sum(r_hsv[:,:,0] * mask_r) / mask_r.sum()
                s_hue = np.sum(s_hsv[:,:,0] * mask_s) / mask_s.sum()
                hue_shift = int(r_hue - s_hue)
                hue_shift = max(-100, min(100, hue_shift))
                
                # Saturation adjustment
                r_sat = np.sum(r_hsv[:,:,1] * mask_r) / mask_r.sum()
                s_sat = np.sum(s_hsv[:,:,1] * mask_s) / mask_s.sum()
                sat_adj = int((r_sat - s_sat) / 2.55)
                sat_adj = max(-100, min(100, sat_adj))
                
                # Luminance adjustment
                r_lum = np.sum(r_hsv[:,:,2] * mask_r) / mask_r.sum()
                s_lum = np.sum(s_hsv[:,:,2] * mask_s) / mask_s.sum()
                lum_adj = int((r_lum - s_lum) / 2.55)
                lum_adj = max(-100, min(100, lum_adj))
                
                hsl[color] = {"Hue": hue_shift, "Saturation": sat_adj, "Luminance": lum_adj}
            else:
                hsl[color] = {"Hue": 0, "Saturation": 0, "Luminance": 0}
        
        return hsl
    
    def calculate_tone_curve(self, r_lab, s_lab):
        """Calculate tone curve adjustments"""
        # Sample points: shadows (25%), midtones (50%), highlights (75%)
        points = []
        for pct in [25, 50, 75]:
            r_val = int(np.percentile(r_lab[:,:,0], pct))
            s_val = int(np.percentile(s_lab[:,:,0], pct))
            # Input is source value, output is reference value
            points.append((s_val, r_val))
        return points
    
    def calculate_color_grading(self, r_lab, s_lab):
        """Calculate color grading (split toning) for shadows, midtones, highlights"""
        grading = {}
        
        # Define masks for shadows, midtones, highlights
        ranges = {
            "Shadows": (0, 85),
            "Midtones": (85, 170),
            "Highlights": (170, 255)
        }
        
        for range_name, (lum_min, lum_max) in ranges.items():
            mask_r = ((r_lab[:,:,0] >= lum_min) & (r_lab[:,:,0] < lum_max)).astype(float)
            mask_s = ((s_lab[:,:,0] >= lum_min) & (s_lab[:,:,0] < lum_max)).astype(float)
            
            if mask_r.sum() > 0 and mask_s.sum() > 0:
                # Get average a and b channels for this range
                r_a = np.sum(r_lab[:,:,1] * mask_r) / mask_r.sum()
                r_b = np.sum(r_lab[:,:,2] * mask_r) / mask_r.sum()
                
                # Convert LAB offset to hue/saturation
                hue = int(np.arctan2(r_b, r_a) * 180 / np.pi)
                if hue < 0: hue += 360
                saturation = int(np.sqrt(r_a**2 + r_b**2) * 2)
                saturation = min(100, saturation)
                
                grading[range_name] = {"Hue": hue, "Saturation": saturation}
            else:
                grading[range_name] = {"Hue": 0, "Saturation": 0}
        
        return grading

    def run(self):
        if self.ref_img is None or self.src_img is None:
            messagebox.showwarning("Warning", "Select both images.")
            return
        try:
            m = self.calculate_metrics()
            
            # Build HSL XML elements
            hsl_xml = ""
            for color, vals in m["HSL"].items():
                hsl_xml += f'    crs:Hue{color}="{vals["Hue"]}"\n'
                hsl_xml += f'    crs:Saturation{color}="{vals["Saturation"]}"\n'
                hsl_xml += f'    crs:Luminance{color}="{vals["Luminance"]}"\n'
            
            # Build Tone Curve Points
            tone_curve_points = " ".join([f"{p[0]}, {p[1]}" for p in m["ToneCurve"]])
            
            # Build Color Grading XML
            cg = m["ColorGrading"]
            color_grading_xml = f'''    crs:SplitToningShadowHue="{cg["Shadows"]["Hue"]}"
    crs:SplitToningShadowSaturation="{cg["Shadows"]["Saturation"]}"
    crs:SplitToningHighlightHue="{cg["Highlights"]["Hue"]}"
    crs:SplitToningHighlightSaturation="{cg["Highlights"]["Saturation"]}"'''
            
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
    crs:Highlights2012="{m["Highlights2012"]}"
    crs:Shadows2012="{m["Shadows2012"]}"
    crs:Whites2012="0"
    crs:Blacks2012="0"
    crs:Temperature="{m["Temperature"]}"
    crs:Tint="{m["Tint"]}"
    crs:Vibrance="{m["Vibrance"]}"
    crs:Saturation="{m["Saturation"]}"
{hsl_xml}{color_grading_xml}
    crs:ParametricShadows="0"
    crs:ParametricDarks="0"
    crs:ParametricLights="0"
    crs:ParametricHighlights="0"
    crs:ParametricShadowSplit="25"
    crs:ParametricMidtoneSplit="50"
    crs:ParametricHighlightSplit="75"
    crs:Sharpness="0"
    crs:LuminanceSmoothing="0"
    crs:ColorNoiseReduction="0"
    crs:HasCrop="False"
    crs:AlreadyApplied="True">
   <crs:ToneCurvePV2012>
    <rdf:Seq>
     <rdf:li>0, 0</rdf:li>
     <rdf:li>{tone_curve_points}</rdf:li>
     <rdf:li>255, 255</rdf:li>
    </rdf:Seq>
   </crs:ToneCurvePV2012>
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
                    f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
                    f.write(b'<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>\n')
                    f.write(xmp_content.encode("utf-8"))
                    f.write(b'\n<?xpacket end="w"?>')
                self.log.insert("end", f"\nSaved: {path}")
                messagebox.showinfo("Success", "Preset saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
