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
        r_hsv = cv2.cvtColor(self.ref_img, cv2.COLOR_BGR2HSV).astype(np.float32)
        s_hsv = cv2.cvtColor(self.src_img, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Enhanced exposure calculation with histogram analysis
        r_mean_lum = np.mean(r_lab[:,:,0])
        s_mean_lum = np.mean(s_lab[:,:,0])
        
        # Zone-based exposure for better accuracy
        r_midtones = np.mean(r_lab[(r_lab[:,:,0] > 85) & (r_lab[:,:,0] < 170)])
        s_midtones = np.mean(s_lab[(s_lab[:,:,0] > 85) & (s_lab[:,:,0] < 170)])
        
        # Weighted exposure: 60% midtones, 40% overall
        if not np.isnan(r_midtones) and not np.isnan(s_midtones):
            exp = (0.6 * (r_midtones - s_midtones) + 0.4 * (r_mean_lum - s_mean_lum)) / 50.0
        else:
            exp = (r_mean_lum - s_mean_lum) / 50.0
        # Enhanced contrast with tonal range analysis        s_std = np.std(s_lab[:,:,0])
        r_std = np.std(r_lab[:,:,0])
        s_std = np.std(s_lab[:,:,0])
                # Calculate tonal range (dynamic range)
        r_range = np.percentile(r_lab[:,:,0], 95) - np.percentile(r_lab[:,:,0], 5)
        s_range = np.percentile(s_lab[:,:,0], 95) - np.percentile(s_lab[:,:,0], 5)
        
        # Combined standard deviation and range-based contrast
        std_contrast_ratio = r_std / (s_std + 1e-6)
        range_contrast_ratio = r_range / (s_range + 1e-6)
        
        # Weighted combination: 70% std, 30% range
        contrast_ratio = 0.7 * std_contrast_ratio + 0.3 * range_contrast_ratio
        contrast = int((contrast_ratio - 1.0) * 100)
        contrast = max(-100, min(100, contrast))
        
        temp = int((np.mean(r_lab[:,:,2]) - np.mean(s_lab[:,:,2])) * 0.5)
        tint = int((np.mean(r_lab[:,:,1]) - np.mean(s_lab[:,:,1])) * 0.5)
        
        r_highlights = np.percentile(r_lab[:,:,0], 90)
        s_highlights = np.percentile(s_lab[:,:,0], 90)
        highlights = int((r_highlights - s_highlights) / 2.55)
        highlights = max(-100, min(100, highlights))
        
        r_shadows = np.percentile(r_lab[:,:,0], 10)
        s_shadows = np.percentile(s_lab[:,:,0], 10)
        shadows = int((r_shadows - s_shadows) / 2.55)
        shadows = max(-100, min(100, shadows))
        
        r_whites = np.percentile(r_lab[:,:,0], 95)
        s_whites = np.percentile(s_lab[:,:,0], 95)
        whites = int((r_whites - s_whites) / 2.55)
        whites = max(-100, min(100, whites))
        
        r_blacks = np.percentile(r_lab[:,:,0], 5)
        s_blacks = np.percentile(s_lab[:,:,0], 5)
        blacks = int((r_blacks - s_blacks) / 2.55)
        blacks = max(-100, min(100, blacks))
        
        r_sat = np.mean(r_hsv[:,:,1])
        s_sat = np.mean(s_hsv[:,:,1])
        saturation = int((r_sat - s_sat) / 2.55)
        saturation = max(-100, min(100, saturation))
        vibrance = int(saturation * 0.7)
        
        texture = int(contrast * 0.3)
        clarity = int(contrast * 0.5)
        dehaze = 0
        
        hsl_adjustments = self.calculate_hsl(r_hsv, s_hsv)
        tone_curve = self.calculate_tone_curve(r_lab, s_lab)
        color_grading = self.calculate_color_grading(r_lab, s_lab)
        calibration = self.calculate_calibration(r_lab, s_lab)
        
        # Detect if reference image is B&W
        ref_is_bw = self.is_black_and_white(self.ref_img)
        src_is_bw = self.is_black_and_white(self.src_img)
        convert_to_grayscale = ref_is_bw and not src_is_bw  # Convert if ref is B&W but src is color
        
        return {
            "Temperature": temp, "Tint": tint,
            "Exposure2012": round(exp, 2), "Contrast2012": contrast,
            "Highlights2012": highlights, "Shadows2012": shadows,
            "Whites2012": whites, "Blacks2012": blacks,
            "Texture": texture, "Clarity": clarity, "Dehaze": dehaze,
            "Vibrance": vibrance, "Saturation": saturation,
            "HSL": hsl_adjustments, "ToneCurve": tone_curve,
            "ColorGrading": color_grading, "Calibration": calibration,
        "ConvertToGrayscale": convert_to_grayscale,
        # Missing Fuji-style parameters
        "Sharpness": 25,  # Default sharpness
        "ShadowTint": 0,  # Shadow color tint
        "GrainAmount": 0,  # Film grain amount (0-100)
        "GrainSize": 25,  # Grain size (0-100)
        "GrainFrequency": 50,  # Grain roughness (0-100)
        "SharpenRadius": 1.0,  # Sharpening radius (0.5-3.0)
        "SharpenDetail": 25,  # Detail amount (0-100)
        "SharpenEdgeMasking": 0,  # Edge masking (0-100)
        "ParametricShadows": 0,  # Parametric shadows (-100 to 100)
        "ParametricDarks": 0,  # Parametric darks (-100 to 100)
        "ParametricLights": 0,  # Parametric lights (-100 to 100)
        "ParametricHighlights": 0,  # Parametric highlights (-100 to 100)
        "ParametricShadowSplit": 25,  # Shadow split point (0-100)
        "ParametricMidtoneSplit": 50,  # Midtone split point (0-100)
        "ParametricHighlightSplit": 75,  # Highlight split point (0-100)
        "SplitToningShadowHue": 0,  # Split toning shadow hue (0-360)
        "SplitToningShadowSaturation": 0,  # Split toning shadow sat (0-100)
        "SplitToningHighlightHue": 0,  # Split toning highlight hue (0-360)
        "SplitToningHighlightSaturation": 0,  # Split toning highlight sat (0-100)
        "SplitToningBalance": 0  # Split toning balance (-100 to 100)
        }
    
    def calculate_hsl(self, r_hsv, s_hsv):
        hsl = {}
        color_ranges = {
            "Red": (0, 22), "Orange": (22, 45), "Yellow": (45, 67),
            "Green": (67, 135), "Aqua": (135, 157),
            "Blue": (157, 247), "Purple": (247, 280), "Magenta": (280, 360)
        }
        
        for color, (h_min, h_max) in color_ranges.items():
            mask_r = ((r_hsv[:,:,0] >= h_min) & (r_hsv[:,:,0] < h_max)).astype(float)
            mask_s = ((s_hsv[:,:,0] >= h_min) & (s_hsv[:,:,0] < h_max)).astype(float)
            
            if mask_r.sum() > 100 and mask_s.sum() > 100:
                r_hue = np.sum(r_hsv[:,:,0] * mask_r) / mask_r.sum()
                s_hue = np.sum(s_hsv[:,:,0] * mask_s) / mask_s.sum()
                hue_shift = int((r_hue - s_hue) / 1.8)
                hue_shift = max(-100, min(100, hue_shift))
                
                r_sat = np.sum(r_hsv[:,:,1] * mask_r) / mask_r.sum()
                s_sat = np.sum(s_hsv[:,:,1] * mask_s) / mask_s.sum()
                sat_adj = int((r_sat - s_sat) / 2.55)
                sat_adj = max(-100, min(100, sat_adj))
                
                r_lum = np.sum(r_hsv[:,:,2] * mask_r) / mask_r.sum()
                s_lum = np.sum(s_hsv[:,:,2] * mask_s) / mask_s.sum()
                lum_adj = int((r_lum - s_lum) / 2.55)
                lum_adj = max(-100, min(100, lum_adj))
                
                hsl[color] = {"Hue": hue_shift, "Saturation": sat_adj, "Luminance": lum_adj}
            else:
                hsl[color] = {"Hue": 0, "Saturation": 0, "Luminance": 0}
        
        return hsl
    
    def calculate_tone_curve(self, r_lab, s_lab):
        points = []
        for pct in [12.5, 25, 50, 75, 87.5]:
            r_val = int(np.percentile(r_lab[:,:,0], pct))
            s_val = int(np.percentile(s_lab[:,:,0], pct))
            points.append((s_val, r_val))
        return points
    
    def calculate_color_grading(self, r_lab, s_lab):
        grading = {}
        ranges = {
            "Shadows": (0, 85), "Midtones": (85, 170), "Highlights": (170, 255)
        }
        
        for range_name, (lum_min, lum_max) in ranges.items():
            mask_r = ((r_lab[:,:,0] >= lum_min) & (r_lab[:,:,0] < lum_max)).astype(float)
            
            if mask_r.sum() > 0:
                r_a = np.sum(r_lab[:,:,1] * mask_r) / mask_r.sum()
                r_b = np.sum(r_lab[:,:,2] * mask_r) / mask_r.sum()
                
                hue = int(np.arctan2(r_b - 128, r_a - 128) * 180 / np.pi)
                if hue < 0: hue += 360
                saturation = int(np.sqrt((r_a - 128)**2 + (r_b - 128)**2) / 1.5)
                saturation = min(100, saturation)
                
                grading[range_name] = {"Hue": hue, "Sat": saturation}
            else:
                grading[range_name] = {"Hue": 0, "Sat": 0}
        
        grading["Balance"] = 0
        return grading
    
    def is_black_and_white(self, img):
        """Detect if image is black & white with improved precision"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
        avg_saturation = np.mean(hsv[:,:,1])
        
        # Method 1: Average saturation check (stricter threshold)
        saturation_check = avg_saturation < 10
        
        # Method 2: Percentile-based check (more robust to outliers)
        p95_saturation = np.percentile(hsv[:,:,1], 95)
        percentile_check = p95_saturation < 20
        
        # Method 3: Standard deviation check (consistent grayscale)
        std_saturation = np.std(hsv[:,:,1])
        std_check = std_saturation < 8
        
        # Method 4: RGB channel correlation (B&W has high correlation)
        b, g, r = cv2.split(img)
        rg_corr = np.corrcoef(r.flatten(), g.flatten())[0,1]
        rb_corr = np.corrcoef(r.flatten(), b.flatten())[0,1]
        gb_corr = np.corrcoef(g.flatten(), b.flatten())[0,1]
        correlation_check = (rg_corr > 0.98 and rb_corr > 0.98 and gb_corr > 0.98)
        
        # Combine multiple methods for higher precision
        # Image is B&W if it passes saturation AND (percentile OR correlation)
        is_bw = saturation_check and (percentile_check or correlation_check)
        
        return is_bw
    def calculate_calibration(self, r_lab, s_lab):
        return {
            "RedHue": 0, "RedSat": 0,
            "GreenHue": 0, "GreenSat": 0,
            "BlueHue": 0, "BlueSat": 0
        }

    def run(self):
        if self.ref_img is None or self.src_img is None:
            messagebox.showwarning("Warning", "Select both images.")
            return
        try:
            m = self.calculate_metrics()
            
            # Build HSL XML with correct attribute names
            hsl_xml = ""
            for color, vals in m["HSL"].items():
                hsl_xml += f'    crs:HueAdjustment{color}="{vals["Hue"]}"\n'
                hsl_xml += f'    crs:SaturationAdjustment{color}="{vals["Saturation"]}"\n'
                hsl_xml += f'    crs:LuminanceAdjustment{color}="{vals["Luminance"]}"\n'
            
            # Build Tone Curve with proper spacing
            tone_points_str = "\n     ".join([f"<rdf:li>{p[0]}, {p[1]}</rdf:li>" for p in m["ToneCurve"]])
            
            # Color Grading
            cg = m["ColorGrading"]
            
            # Calibration
            cal = m["Calibration"]
            
            xmp_content = f"""<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 7.0-c000 79.daa7c53, 2021/02/18-15:30:12        ">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:crs="http://ns.adobe.com/camera-raw-settings/1.0/"
    crs:Temp="{m["Temperature"]}"
    crs:Tint="{m["Tint"]}"
    crs:Exposure2012="{m["Exposure2012"]}"
    crs:Contrast2012="{m["Contrast2012"]}"
    crs:Highlights2012="{m["Highlights2012"]}"
    crs:Shadows2012="{m["Shadows2012"]}"
    crs:Whites2012="{m["Whites2012"]}"
    crs:Blacks2012="{m["Blacks2012"]}"
    crs:Texture="{m["Texture"]}"
    crs:Clarity="{m["Clarity"]}"
    crs:Dehaze="{m["Dehaze"]}"
    crs:Vibrance="{m["Vibrance"]}"
    crs:Saturation="{m["Saturation"]}"
{hsl_xml}    crs:ColorGradeShadowsHue="{cg["Shadows"]["Hue"]}"
    crs:ColorGradeShadowsSat="{cg["Shadows"]["Sat"]}"
    crs:ColorGradeMidtonesHue="{cg["Midtones"]["Hue"]}"
    crs:ColorGradeMidtonesSat="{cg["Midtones"]["Sat"]}"
    crs:ColorGradeHighlightsHue="{cg["Highlights"]["Hue"]}"
    crs:ColorGradeHighlightsSat="{cg["Highlights"]["Sat"]}"
    crs:ColorGradeBalance="{cg["Balance"]}"
Add missing Fuji film preset parameters    crs:RedPrimarySat="{cal["RedSat"]}"
    crs:GreenPrimaryHue="{cal["GreenHue"]}"
    crs:GreenPrimarySat="{cal["GreenSat"]}"
    crs:BluePrimaryHue="{cal["BlueHue"]}"
    crs:BluePrimarySat="{cal["BlueSat"]}""
    crs:ConvertToGrayscale="{str(m["ConvertToGrayscale"]).lower()}"
     crs:Sharpness="{m["Sharpness"]}"
     crs:ShadowTint="{m["ShadowTint"]}"
     crs:GrainAmount="{m["GrainAmount"]}"
     crs:GrainSize="{m["GrainSize"]}"
     crs:GrainFrequency="{m["GrainFrequency"]}"
     crs:SharpenRadius="{m["SharpenRadius"]}"
     crs:SharpenDetail="{m["SharpenDetail"]}"
     crs:SharpenEdgeMasking="{m["SharpenEdgeMasking"]}"
     crs:ParametricShadows="{m["ParametricShadows"]}"
     crs:ParametricDarks="{m["ParametricDarks"]}"
     crs:ParametricLights="{m["ParametricLights"]}"
     crs:ParametricHighlights="{m["ParametricHighlights"]}"
     crs:ParametricShadowSplit="{m["ParametricShadowSplit"]}"
     crs:ParametricMidtoneSplit="{m["ParametricMidtoneSplit"]}"
     crs:ParametricHighlightSplit="{m["ParametricHighlightSplit"]}"
     crs:SplitToningShadowHue="{m["SplitToningShadowHue"]}"
     crs:SplitToningShadowSaturation="{m["SplitToningShadowSaturation"]}"
     crs:SplitToningHighlightHue="{m["SplitToningHighlightHue"]}"
     crs:SplitToningHighlightSaturation="{m["SplitToningHighlightSaturation"]}"
     crs:SplitToningBalance="{m["SplitToningBalance"]}">
   <crs:ToneCurvePV2012>
     <rdf:li>0, 0</rdf:li>
     {tone_points_str}
     <rdf:li>255, 255</rdf:li>
   </crs:ToneCurvePV2012>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>"""
            
            path = filedialog.asksaveasfilename(defaultextension=".xmp", filetypes=[("XMP files", "*.xmp")])
            if path:
                with open(path, "wb") as f:
                    f.write(b'\xef\xbb\xbf')
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
