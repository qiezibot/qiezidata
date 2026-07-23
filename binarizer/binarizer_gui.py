#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片二值化工具 v1.2 - ADB截图 + A*寻路 + 7种算法 + 批量处理
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import subprocess
import os
import sys
import tempfile
import heapq
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageDraw
import numpy as np

# ── ADB ────────────────────────────────────────────────────────

ADB_PATHS = [
    r"C:\Users\lfy20\Downloads\scrcpy-win64-v1.24\adb.exe",
    r"C:\Users\lfy20\Downloads\QtScrcpy-win-x86-v2.1.2\QtScrcpy-win-x86-v2.1.2\adb.exe",
    r"C:\Program Files (x86)\aztp\Resources\adb.exe",
]
ADB_EXE = None
for p in ADB_PATHS:
    if os.path.isfile(p): ADB_EXE = p; break

def adb_screenshot(out_path):
    if not ADB_EXE: return False
    try:
        r = subprocess.run([ADB_EXE, "exec-out", "screencap", "-p"], capture_output=True, timeout=15)
        if r.returncode != 0 or len(r.stdout) < 100: return False
        with open(out_path, "wb") as f: f.write(r.stdout)
        return os.path.getsize(out_path) > 1000
    except: return False


# ── 核心引擎 ──────────────────────────────────────────────────

class Binarizer:
    METHODS = {
        "Otsu": "otsu",
        "Triangle": "triangle",
        "自适应(Avg-C)": "adaptive",
        "全局阈值": "global",
        "Intermodes": "intermodes",
        "Kapur熵": "entropy",
        "MinimumError": "minerror",
        "颜色分割(绿排除)": "color_green",
    }

    @staticmethod
    def otsu_threshold(arr):
        hist, _ = np.histogram(arr, bins=256, range=(0, 256))
        total = arr.size
        if total == 0: return 128
        sum_total = np.dot(np.arange(256), hist)
        sb, wb = 0, 0
        max_var, best = 0, 0
        for t in range(256):
            wb += hist[t]
            if wb == 0: continue
            wf = total - wb
            if wf == 0: break
            sb += t * hist[t]
            mb = sb / wb; mf = (sum_total - sb) / wf
            var = wb * wf * (mb - mf) ** 2
            if var > max_var: max_var, best = var, t
        return best

    @staticmethod
    def triangle_threshold(arr):
        hist, _ = np.histogram(arr, bins=256, range=(0,256))
        peak = int(np.argmax(hist)); pv = int(hist[peak])
        left = next(i for i in range(256) if hist[i] > 0)
        right = next(i for i in range(255,-1,-1) if hist[i] > 0)
        x1,y1 = (left,0) if peak-left >= right-peak else (right,0)
        x2,y2 = peak, pv
        md, best = 0, 0
        step = 1 if x2 >= x1 else -1
        for x in range(x1, x2+step, step):
            d = abs((y2-y1)*x - (x2-x1)*int(hist[x]) + x2*y1 - y2*x1)
            if d > md: md,best = d,x
        return best

    @staticmethod
    def intermodes_threshold(arr):
        hist, _ = np.histogram(arr, bins=256, range=(0,256))
        hist = hist.astype(np.float64)
        kernel = np.array([1,2,1], dtype=np.float64)/4.0
        for _ in range(5): hist[1:-1] = np.convolve(hist,kernel,mode="same")[1:-1]
        peaks = [(i,hist[i]) for i in range(1,255) if hist[i]>hist[i-1] and hist[i]>=hist[i+1]]
        if len(peaks) >= 2:
            peaks.sort(key=lambda x:-x[1])
            return (peaks[0][0]+peaks[1][0])//2
        return Binarizer.otsu_threshold(arr)

    @staticmethod
    def entropy_threshold(arr):
        hist,_ = np.histogram(arr,bins=256,range=(0,256))
        total=arr.size; best,me=0,0
        for t in range(1,255):
            bg=int(hist[:t].sum()); fg=int(hist[t:].sum())
            if bg<1 or fg<1: continue
            pb=hist[:t]/bg; pf=hist[t:]/fg
            pb=pb[pb>0]; pf=pf[pf>0]
            e=-np.sum(pb*np.log2(pb))-np.sum(pf*np.log2(pf))
            if e>me: me,best=e,t
        return best

    @staticmethod
    def minerror_threshold(arr):
        hist,_=np.histogram(arr,bins=256,range=(0,256))
        total=arr.size; best,mj=0,float("inf")
        for t in range(1,255):
            bg=int(hist[:t].sum()); fg=int(hist[t:].sum())
            if bg<1 or fg<1: continue
            mb=np.dot(np.arange(t),hist[:t])/bg
            vb=np.dot((np.arange(t)-mb)**2,hist[:t])/bg
            mf=np.dot(np.arange(t,256),hist[t:])/fg
            vf=np.dot((np.arange(t,256)-mf)**2,hist[t:])/fg
            if vb<1e-6 or vf<1e-6: continue
            j=1+2*(bg/total*np.log(vb)+fg/total*np.log(vf))-2*(bg/total*np.log(bg/total)+fg/total*np.log(fg/total))
            if j<mj: mj,best=j,t
        return best

    @staticmethod
    def adaptive_threshold(arr, window=31, c=10):
        h,w=arr.shape; half=window//2
        integral=np.cumsum(np.cumsum(arr.astype(np.int64),axis=0),axis=1)
        out=np.zeros_like(arr,dtype=np.uint8)
        for y in range(h):
            y1,y2=max(0,y-half),min(h-1,y+half)
            for x in range(w):
                x1,x2=max(0,x-half),min(w-1,x+half)
                area=(x2-x1+1)*(y2-y1+1)
                a=integral[y2,x2]; b=integral[y1-1,x2] if y1>0 else 0
                cc=integral[y2,x1-1] if x1>0 else 0; d=integral[y1-1,x1-1] if y1>0 and x1>0 else 0
                th=(a-b-cc+d)//area-c
                out[y,x]=255 if arr[y,x]>th else 0
        return out

    @staticmethod
    def _clahe(arr,tile=64,clip=40):
        h,w=arr.shape; out=arr.copy().astype(np.float64)
        for y in range(0,h,tile):
            for x in range(0,w,tile):
                x2,y2=min(x+tile,w),min(y+tile,h)
                t=arr[y:y2,x:x2]; hist,_=np.histogram(t,bins=256,range=(0,256))
                cl=clip*t.size//256; ex=int(np.sum(np.maximum(hist-cl,0)))
                hist=np.minimum(hist,cl)+ex//256; cdf=hist.cumsum()
                cdf=(cdf-cdf.min())/(cdf.max()-cdf.min()+1e-6)*255
                out[y:y2,x:x2]=cdf[t]
        return np.clip(out,0,255).astype(np.uint8)

    @staticmethod
    def unsharp_mask(arr, amount=1.0, radius=1.0):
        blur=np.array(Image.fromarray(arr).filter(ImageFilter.GaussianBlur(radius=radius)),dtype=np.uint8)
        return np.clip(arr+amount*(arr.astype(np.int16)-blur.astype(np.int16)),0,255).astype(np.uint8)

    @staticmethod
    def auto_contrast(arr, low_pct=2, high_pct=98):
        low=int(np.percentile(arr,low_pct)); high=int(np.percentile(arr,high_pct))
        if high-low<1: return arr
        return np.clip((arr.astype(np.float64)-low)/(high-low)*255,0,255).astype(np.uint8)

    # ── A* 寻路 ──────────────────────────────────────────────

    @staticmethod
    def astar(grid_img, start, goal, allow_diagonal=True):
        """
        A* 寻路
        grid_img: 二值图 PIL Image (L), 255=可走, 0=障碍
        start, goal: (x, y) 像素坐标
        返回 [(x,y), ...] 路径 或 None（无路） 或 "blocked"（起点/终点是障碍）
        """
        arr = np.array(grid_img, dtype=np.uint8)
        h, w = arr.shape
        s = (int(start[1]), int(start[0]))
        g = (int(goal[1]), int(goal[0]))
        if s[0]<0 or s[0]>=h or s[1]<0 or s[1]>=w: return None
        if g[0]<0 or g[0]>=h or g[1]<0 or g[1]>=w: return None
        if arr[s] != 255: return "blocked_s"
        if arr[g] != 255: return "blocked_g"

        nb = [(0,1),(0,-1),(1,0),(-1,0)]
        if allow_diagonal: nb += [(1,1),(1,-1),(-1,1),(-1,-1)]
        def heu(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])

        open_set = [(0,s)]
        came_from = {}
        g_score = {s:0}
        f_score = {s:heu(s,g)}

        while open_set:
            _,cur = heapq.heappop(open_set)
            if cur == g:
                path = []
                while cur in came_from:
                    path.append(cur); cur=came_from[cur]
                path.append(s); path.reverse()
                return [(p[1],p[0]) for p in path]
            for dx,dy in nb:
                nx,ny = cur[0]+dx, cur[1]+dy
                nb_ = (nx,ny)
                if nx<0 or nx>=h or ny<0 or ny>=w: continue
                if arr[nb_] != 255: continue
                if allow_diagonal and dx!=0 and dy!=0:
                    if arr[(cur[0]+dx,cur[1])]!=255 and arr[(cur[0],cur[1]+dy)]!=255: continue
                tg = g_score[cur] + (1.414 if dx!=0 and dy!=0 else 1)
                if tg < g_score.get(nb_, float('inf')):
                    came_from[nb_]=cur; g_score[nb_]=tg
                    hh=tg+heu(nb_,g)
                    f_score[nb_]=hh; heapq.heappush(open_set,(hh,nb_))
        return None

    @staticmethod
    def draw_path(img, path, line_width=3):
        if path is None: return img
        r=img.copy()
        if r.mode!="RGB": r=r.convert("RGB")
        draw=ImageDraw.Draw(r)
        draw.line([(p[0],p[1]) for p in path], fill=(255,0,0), width=line_width)
        lw=max(line_width+2,5)
        sx,sy=path[0]; gx,gy=path[-1]
        draw.ellipse([sx-lw,sy-lw,sx+lw,sy+lw], fill=(0,255,0))
        draw.ellipse([gx-lw,gy-lw,gx+lw,gy+lw], fill=(255,0,0))
        return r

    @staticmethod
    def process(img, method="otsu", threshold=128, window=31, c_val=10,
                blur_sigma=0, equalize=False, clahe=False, invert=False,
                sharpness=0, contrast_stretch=False):
        gray=img.convert("L"); arr=np.array(gray,dtype=np.uint8)
        if contrast_stretch: arr=Binarizer.auto_contrast(arr)
        if equalize: arr=np.array(ImageEnhance.Contrast(Image.fromarray(arr)).enhance(1.5),dtype=np.uint8)
        if clahe: arr=Binarizer._clahe(arr)
        if sharpness>0: arr=Binarizer.unsharp_mask(arr,amount=sharpness,radius=1.0)
        if blur_sigma>0: arr=np.array(Image.fromarray(arr).filter(ImageFilter.GaussianBlur(radius=blur_sigma)),dtype=np.uint8)
        if method=="global": r=np.where(arr>threshold,255,0).astype(np.uint8)
        elif method=="adaptive": r=Binarizer.adaptive_threshold(arr,window,c_val)
        elif method=="otsu": r=np.where(arr>Binarizer.otsu_threshold(arr),255,0).astype(np.uint8)
        elif method=="triangle": r=np.where(arr>Binarizer.triangle_threshold(arr),255,0).astype(np.uint8)
        elif method=="intermodes": r=np.where(arr>Binarizer.intermodes_threshold(arr),255,0).astype(np.uint8)
        elif method=="entropy": r=np.where(arr>Binarizer.entropy_threshold(arr),255,0).astype(np.uint8)
        elif method=="minerror": r=np.where(arr>Binarizer.minerror_threshold(arr),255,0).astype(np.uint8)
        elif method=="color_green":
            # 颜色分割：原图RGB中排除绿色区域（树等），剩下的灰度二值化
            rgb=img.convert("RGB"); arr_rgb=np.array(rgb)
            g=arr_rgb[:,:,1].astype(np.int16); r2=arr_rgb[:,:,0].astype(np.int16); b=arr_rgb[:,:,2].astype(np.int16)
            # 绿色：G > R+20 且 G > B+20 且 G > 80
            green_mask=(g > r2+20) & (g > b+20) & (g > 80)
            # 灰度图上排除绿色区域后再二值化
            gray=img.convert("L"); arr=np.array(gray,dtype=np.uint8)
            if contrast_stretch: arr=Binarizer.auto_contrast(arr)
            if sharpness>0: arr=Binarizer.unsharp_mask(arr,amount=sharpness,radius=1.0)
            # 排除绿色后用Otsu
            masked=arr.copy()
            masked[green_mask]=255  # 绿色区域变白（可走）
            otsu_th=Binarizer.otsu_threshold(masked)
            r=np.where(arr>otsu_th,255,0).astype(np.uint8)
            r[green_mask]=255  # 绿色区域强制可走
        else: r=np.where(arr>128,255,0).astype(np.uint8)
        if invert: r=255-r
        return Image.fromarray(r,mode="L")


# ── GUI ─────────────────────────────────────────────────────────

class BinarizerApp:
    def __init__(self, root):
        self.root=root
        root.title("图片二值化工具 v1.2")
        root.geometry("1200x750"); root.minsize(900,600)

        self.current_image=None
        self.preview_image=None
        self.original_image=None
        self.original_path=None
        self.batch_files=[]
        self._preview_tk=None
        self.zoom_factor=1.0
        self.history=[]; self.history_idx=-1
        self.processing=False; self.auto_timer=None
        self._drag_data={"x":0,"y":0}

        # A*
        self.astar_mode=False
        self.astar_start=None
        self.astar_goal=None
        self.astar_path=None
        self.astar_overlay=None

        # 编辑模式
        self.edit_mode=False
        self.edit_color_var=tk.StringVar(value="white")
        self.brush_var=tk.IntVar(value=5)

        # 配置文件
        self.config_path = os.path.join(os.path.dirname(__file__), "settings.json")

        self._build_ui()
        self._load_settings()
        self._update_status("就绪")
        if ADB_EXE:
            ok=self._check_adb()
            self._update_status(f"ADB: {Path(ADB_EXE).name}"+(" | 设备在线" if ok else " | 无设备"))
            self.adb_lbl.config(text="设备在线" if ok else "无设备", foreground="green" if ok else "red")
        else:
            self._log("未找到 ADB")

    def _check_adb(self):
        if not ADB_EXE: return False
        try:
            r=subprocess.run([ADB_EXE,"devices"],capture_output=True,timeout=5,text=True)
            return "device" in r.stdout
        except: return False

    def _refresh_adb(self):
        ok = self._check_adb()
        self.adb_lbl.config(text="设备在线" if ok else "无设备",foreground="green" if ok else "red")
        self._update_status("ADB已刷新 - 设备在线" if ok else "ADB: 无设备，请检查USB连接")

    def _save_settings(self):
        import json
        data = {
            "method": self.method_var.get(),
            "threshold": self.th_var.get(),
            "window": self.win_var.get(),
            "c_val": self.c_var.get(),
            "blur_sigma": self.blur_var.get(),
            "sharpness": self.sharp_var.get(),
            "equalize": self.eq_var.get(),
            "clahe": self.cl_var.get(),
            "contrast_stretch": self.cs_var.get(),
            "invert": self.inv_var.get(),
            "joystick_x": self.jx_var.get(),
            "joystick_y": self.jy_var.get(),
            "allow_diagonal": self.ad_var.get(),
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._update_status("配置已保存")
        except Exception as e:
            self._update_status(f"保存失败: {e}")

    def _load_settings(self):
        import json
        if not os.path.isfile(self.config_path):
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "method" in data:
                mlist = list(Binarizer.METHODS.keys())
                if data["method"] in mlist:
                    self.method_var.set(data["method"])
                    self._on_method_change()
            if "threshold" in data: self.th_var.set(data["threshold"])
            if "window" in data: self.win_var.set(data["window"])
            if "c_val" in data: self.c_var.set(data["c_val"])
            if "blur_sigma" in data: self.blur_var.set(float(data["blur_sigma"]))
            if "sharpness" in data: self.sharp_var.set(float(data["sharpness"]))
            if "equalize" in data: self.eq_var.set(data["equalize"])
            if "clahe" in data: self.cl_var.set(data["clahe"])
            if "contrast_stretch" in data: self.cs_var.set(data["contrast_stretch"])
            if "invert" in data: self.inv_var.set(data["invert"])
            if "joystick_x" in data: self.jx_var.set(data["joystick_x"])
            if "joystick_y" in data: self.jy_var.set(data["joystick_y"])
            if "allow_diagonal" in data: self.ad_var.set(bool(data["allow_diagonal"]))
            self._update_status("配置已加载")
        except Exception as e:
            self._update_status(f"加载配置失败: {e}")

    def _log(self,msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end",msg+"\n"); self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _update_status(self,msg):
        self.status_var.set(msg); self.root.update_idletasks()

    def _build_ui(self):
        self.root.grid_rowconfigure(0,weight=1)
        self.root.grid_columnconfigure(1,weight=1)

        left=ttk.Frame(self.root,width=260,padding=6)
        left.grid(row=0,column=0,sticky="nsew"); left.grid_propagate(False)
        row=0
        ttk.Label(left,text="控制面板",font=("微软雅黑",10,"bold")).grid(row=row,column=0,pady=(0,4),sticky="w"); row+=1

        # ── 操作区 ──
        op=ttk.LabelFrame(left,text="操作",padding=4)
        op.grid(row=row,column=0,sticky="ew",pady=1); row+=1
        ttk.Button(op,text="打开图片",command=self._open_image,width=22).pack(fill="x",pady=0)
        ttk.Button(op,text="保存结果",command=self._save_image,width=22).pack(fill="x",pady=0)
        ttk.Button(op,text="批量处理",command=self._batch_select,width=22).pack(fill="x",pady=0)
        ttk.Button(op,text="截图 + 二值化",command=self._adb_capture,width=22).pack(fill="x",pady=0)
        self.adb_lbl=ttk.Label(op,text="",foreground="gray",font=("",8)); self.adb_lbl.pack(fill="x")
        adbrow=ttk.Frame(op); adbrow.pack(fill="x")
        ttk.Button(adbrow,text="刷新ADB",command=self._refresh_adb,width=22).pack(fill="x")

        # ── A* + 编辑 + 模拟 ──
        ae=ttk.LabelFrame(left,text="A*/编辑/模拟",padding=4)
        ae.grid(row=row,column=0,sticky="ew",pady=1); row+=1
        # 第一行：设起点 + 清除
        r1=ttk.Frame(ae); r1.pack(fill="x")
        self.astar_btn=ttk.Button(r1,text="设起点",command=self._toggle_astar,width=10)
        self.astar_btn.pack(side="left",padx=1)
        self.astar_clear=ttk.Button(r1,text="清路径",command=self._clear_astar,width=8)
        self.astar_clear.pack(side="left",padx=1)
        self.sim_btn=ttk.Button(r1,text="▶走",command=self._simulate_walk,width=4)
        self.sim_btn.pack(side="right",padx=1)
        # 第二行：编辑 + 画笔
        r2=ttk.Frame(ae); r2.pack(fill="x")
        self.edit_btn=ttk.Button(r2,text="✏编辑",command=self._toggle_edit,width=8)
        self.edit_btn.pack(side="left",padx=1)
        ttk.Radiobutton(r2,text="白",variable=self.edit_color_var,value="white").pack(side="left")
        ttk.Radiobutton(r2,text="黑",variable=self.edit_color_var,value="black").pack(side="left")
        ttk.Label(r2,text="笔:").pack(side="left",padx=(4,0))
        ttk.Spinbox(r2,from_=1,to=30,textvariable=self.brush_var,width=3).pack(side="left")
        ttk.Label(r2,text="对角:").pack(side="left",padx=(4,0))
        self.ad_var=tk.BooleanVar(value=True)
        ttk.Checkbutton(r2,variable=self.ad_var).pack(side="left")
        # 第三行：信息
        self.astar_info=ttk.Label(ae,text="关闭",foreground="gray",font=("",8))
        self.astar_info.pack(anchor="w")
        # 摇杆
        r3=ttk.Frame(ae); r3.pack(fill="x")
        ttk.Label(r3,text="摇杆").pack(side="left")
        self.jx_var=tk.IntVar(value=417)
        self.jy_var=tk.IntVar(value=792)
        ttk.Spinbox(r3,from_=0,to=2000,textvariable=self.jx_var,width=5).pack(side="left",padx=1)
        ttk.Spinbox(r3,from_=0,to=2000,textvariable=self.jy_var,width=5).pack(side="left",padx=1)

        # ── 二值化方法 ──
        f2=ttk.LabelFrame(left,text="二值化",padding=4)
        f2.grid(row=row,column=0,sticky="ew",pady=2); row+=1
        self.method_var=tk.StringVar(value="Otsu")
        self.mc=ttk.Combobox(f2,textvariable=self.method_var,values=list(Binarizer.METHODS.keys()),state="readonly",width=22)
        self.mc.pack(fill="x",pady=1)
        self.mc.bind("<<ComboboxSelected>>",self._on_method_change); self.mc.current(0)

        self.th_frame=ttk.Frame(f2)
        ttk.Label(self.th_frame,text="阈值:").pack(side="left")
        self.th_var=tk.IntVar(value=128)
        ttk.Scale(self.th_frame,from_=0,to=255,variable=self.th_var,orient="horizontal",command=self._on_param_change).pack(side="left",fill="x",expand=True,padx=4)
        self.th_lbl=ttk.Label(self.th_frame,text="128",width=3); self.th_lbl.pack(side="right")

        self.ad_frame=ttk.LabelFrame(f2,text="自适应参数",padding=4)
        ttk.Label(self.ad_frame,text="窗口:").grid(row=0,column=0,sticky="w")
        self.win_var=tk.IntVar(value=31)
        ttk.Spinbox(self.ad_frame,from_=3,to=199,textvariable=self.win_var,width=6,increment=2).grid(row=0,column=1,padx=2)
        ttk.Label(self.ad_frame,text="C:").grid(row=0,column=2,padx=(8,0))
        self.c_var=tk.IntVar(value=10)
        ttk.Spinbox(self.ad_frame,from_=-50,to=50,textvariable=self.c_var,width=6).grid(row=0,column=3,padx=2)

        # ── 参数区 ──
        pm=ttk.LabelFrame(left,text="参数",padding=4)
        pm.grid(row=row,column=0,sticky="ew",pady=1); row+=1
        # 模糊+锐化一行
        pr1=ttk.Frame(pm); pr1.pack(fill="x")
        ttk.Label(pr1,text="模糊:",font=("",8)).pack(side="left")
        self.blur_var=tk.DoubleVar(value=0)
        ttk.Scale(pr1,from_=0,to=5,variable=self.blur_var,orient="horizontal",command=self._on_param_change).pack(side="left",fill="x",expand=True,padx=2)
        self.blur_lbl=ttk.Label(pr1,text="0",width=2,font=("",8)); self.blur_lbl.pack(side="right")
        ttk.Label(pr1,text="锐:",font=("",8)).pack(side="left",padx=(4,0))
        self.sharp_var=tk.DoubleVar(value=0)
        ttk.Scale(pr1,from_=0,to=3,variable=self.sharp_var,orient="horizontal",command=self._on_param_change).pack(side="left",fill="x",expand=True,padx=2)
        self.sharp_lbl=ttk.Label(pr1,text="0",width=2,font=("",8)); self.sharp_lbl.pack(side="right")
        # 复选框一行
        pr2=ttk.Frame(pm); pr2.pack(fill="x")
        self.eq_var=tk.BooleanVar(value=False); self.cl_var=tk.BooleanVar(value=False); self.cs_var=tk.BooleanVar(value=False); self.inv_var=tk.BooleanVar(value=False)
        ttk.Checkbutton(pr2,text="均衡",variable=self.eq_var,command=self._on_param_change).pack(side="left")
        ttk.Checkbutton(pr2,text="CLAHE",variable=self.cl_var,command=self._on_param_change).pack(side="left")
        ttk.Checkbutton(pr2,text="对比度",variable=self.cs_var,command=self._on_param_change).pack(side="left")
        ttk.Checkbutton(pr2,text="反转",variable=self.inv_var,command=self._on_param_change).pack(side="left")
        # 执行按钮一行
        pr3=ttk.Frame(pm); pr3.pack(fill="x",pady=(2,0))
        ttk.Button(pr3,text="执行",command=self._process,width=6).pack(side="left",padx=1)
        ttk.Button(pr3,text="撤销",command=self._undo,width=4).pack(side="left",padx=1)
        ttk.Button(pr3,text="重做",command=self._redo,width=4).pack(side="left",padx=1)
        ttk.Button(pr3,text="💾保存",command=self._save_settings,width=5).pack(side="right",padx=1)
        ttk.Button(pr3,text="📂加载",command=self._load_settings,width=5).pack(side="right",padx=1)
        ttk.Label(pr3,text="",font=("",8)).pack(side="left",fill="x",expand=True)  # 占位

        # ── 信息 ──
        info_f=ttk.LabelFrame(left,text="信息",padding=2)
        info_f.grid(row=row,column=0,sticky="ew",pady=1); row+=1
        self.info_text=ttk.Label(info_f,text="",font=("",8),anchor="w",justify="left")
        self.info_text.pack(fill="x")

        # 状态栏
        self.status_var=tk.StringVar(value="就绪")
        tk.Label(self.root,textvariable=self.status_var,bg="#007acc",fg="white",anchor="w",padx=8).grid(row=1,column=0,columnspan=2,sticky="ew")

        # 预览区
        right=ttk.Frame(self.root,padding=4)
        right.grid(row=0,column=1,sticky="nsew")
        right.grid_rowconfigure(1,weight=1); right.grid_columnconfigure(0,weight=1)

        tb=ttk.Frame(right)
        tb.grid(row=0,column=0,sticky="ew",pady=(0,4))
        self.view_var=tk.StringVar(value="result")
        for txt,val in [("原图","original"),("结果","result"),("并排对比","side")]:
            ttk.Radiobutton(tb,text=txt,variable=self.view_var,value=val,command=self._on_view_change).pack(side="left",padx=2)
        ttk.Separator(tb,orient="vertical").pack(side="left",fill="y",padx=6)
        ttk.Button(tb,text="+",command=self._zoom_in,width=3).pack(side="left")
        self.zlbl=ttk.Label(tb,text="100%",width=5); self.zlbl.pack(side="left",padx=2)
        ttk.Button(tb,text="-",command=self._zoom_out,width=3).pack(side="left")
        ttk.Button(tb,text="适应",command=self._zoom_fit,width=4).pack(side="left",padx=2)
        ttk.Button(tb,text="1:1",command=self._zoom_actual,width=3).pack(side="left")
        self.file_lbl=ttk.Label(tb,text=""); self.file_lbl.pack(side="right",padx=4)

        cf=ttk.Frame(right,relief="sunken",borderwidth=2)
        cf.grid(row=1,column=0,sticky="nsew")
        cf.grid_rowconfigure(0,weight=1); cf.grid_columnconfigure(0,weight=1)
        self.canvas=tk.Canvas(cf,bg="#2d2d2d",highlightthickness=0,cursor="crosshair")
        self.canvas.grid(row=0,column=0,sticky="nsew")
        self.canvas.bind("<ButtonPress-1>",self._canvas_click)
        self.canvas.bind("<B1-Motion>",self._drag_move)
        self.canvas.bind("<MouseWheel>",self._scroll)
        hs=ttk.Scrollbar(cf,orient="horizontal",command=self.canvas.xview)
        vs=ttk.Scrollbar(cf,orient="vertical",command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hs.set,yscrollcommand=vs.set)
        hs.grid(row=1,column=0,sticky="ew"); vs.grid(row=0,column=1,sticky="ns")

        self.log_frame=ttk.Frame(self.root)
        self.log_frame.grid(row=2,column=0,columnspan=2,sticky="ew")
        self.log_text=ScrolledText(self.log_frame,height=6,state="disabled",font=("Consolas",9))
        self.log_text.pack(fill="both",expand=True)
        self.log_frame.grid_remove()

        self.ad_frame.pack_forget(); self.th_frame.pack_forget()

    def _update_info(self):
        if not self.original_image: return
        w,h=self.original_image.size
        path=self.original_path or Path("?")
        try: sz=os.path.getsize(path)
        except: sz=0
        ss=f"{sz//1024}KB" if sz<1024*1024 else f"{sz/1024/1024:.1f}MB"
        info=f"{path.name} | {w}x{h} | {ss}"
        self.info_text.config(text=info)

    def _on_method_change(self,e=None):
        m=Binarizer.METHODS.get(self.method_var.get(),"otsu")
        self.th_frame.pack_forget(); self.ad_frame.pack_forget()
        if m=="global": self.th_frame.pack(fill="x",pady=2)
        elif m=="adaptive": self.ad_frame.pack(fill="x",pady=2)
        self._on_param_change()

    def _on_param_change(self,e=None):
        self.blur_lbl.config(text=f"{self.blur_var.get():.1f}")
        self.sharp_lbl.config(text=f"{self.sharp_var.get():.1f}")
        self.th_lbl.config(text=str(self.th_var.get()))
        if self.current_image and not self.processing:
            if self.auto_timer: self.root.after_cancel(self.auto_timer)
            self.auto_timer=self.root.after(300,self._process)

    def _open_image(self):
        p=filedialog.askopenfilename(title="选择图片",filetypes=[("图片文件","*.png *.jpg *.jpeg *.bmp *.webp"),("所有文件","*.*")])
        if p: self._load_image(Path(p))

    def _load_image(self,path):
        try:
            self.original_image=Image.open(path).copy(); self.original_path=path
            self.current_image=self.original_image.copy()
            self.history.clear(); self.history_idx=-1
            self._push_history(self.original_image.copy(),"加载原图")
            self._clear_astar()
            self._update_info(); self._update_preview()
            self._update_status(f"已加载: {path.name}")
            self.file_lbl.config(text=f"  {path.name}")
            self._on_method_change()
        except Exception as e: messagebox.showerror("错误",f"无法打开:\n{e}")

    def _save_image(self):
        if not self.current_image: return messagebox.showinfo("提示","请先处理图片")
        img=self.astar_overlay if (self.astar_path and self.astar_overlay) else self.current_image
        default="result_bin.png"
        if self.original_path: default=f"{self.original_path.stem}_bin.png"
        p=filedialog.asksaveasfilename(title="保存",initialfile=default,defaultextension=".png",
            filetypes=[("PNG","*.png"),("JPEG","*.jpg"),("BMP","*.bmp"),("所有文件","*.*")])
        if not p: return
        try: img.save(p); self._update_status(f"已保存: {Path(p).name}")
        except Exception as e: messagebox.showerror("错误",f"保存失败:\n{e}")

    def _batch_select(self):
        files=filedialog.askopenfilenames(title="选择图片",filetypes=[("图片文件","*.png *.jpg *.jpeg *.bmp *.webp"),("所有文件","*.*")])
        if not files: return
        self.batch_files=[Path(f) for f in files]
        out=filedialog.askdirectory(title="输出目录")
        if not out: return
        self._load_image(self.batch_files[0])
        self._run_batch(Path(out))

    def _run_batch(self,out_dir):
        if self.processing: return
        self.processing=True; self.log_frame.grid()
        self._log(f"批量处理 {len(self.batch_files)} 个文件..."); self._log(f"  输出: {out_dir}")
        def worker():
            m=Binarizer.METHODS.get(self.method_var.get(),"otsu"); ok=0
            for i,p in enumerate(self.batch_files):
                try:
                    r=Binarizer.process(Image.open(p).copy(),m,
                        threshold=self.th_var.get(),window=self.win_var.get(),c_val=self.c_var.get(),
                        blur_sigma=self.blur_var.get(),equalize=self.eq_var.get(),clahe=self.cl_var.get(),
                        invert=self.inv_var.get(),sharpness=self.sharp_var.get(),contrast_stretch=self.cs_var.get())
                    r.save(out_dir/f"{p.stem}_bin.png","PNG"); ok+=1
                    self._log(f"  OK [{i+1}] {p.name}")
                    if i==len(self.batch_files)-1: self.current_image=r; self.root.after(0,self._update_preview)
                except Exception as e: self._log(f"  FAIL [{i+1}] {p.name} - {e}")
            self.processing=False
            self._log(f"完成: {ok}/{len(self.batch_files)}"); self._update_status(f"批量完成 {ok}/{len(self.batch_files)}")
        threading.Thread(target=worker,daemon=True).start()

    def _process(self,e=None):
        if not self.original_image or self.processing: return
        self.processing=True; m=Binarizer.METHODS.get(self.method_var.get(),"otsu")
        self._update_status("处理中...")
        def worker():
            try:
                r=Binarizer.process(self.original_image,m,
                    threshold=self.th_var.get(),window=self.win_var.get(),c_val=self.c_var.get(),
                    blur_sigma=self.blur_var.get(),equalize=self.eq_var.get(),clahe=self.cl_var.get(),
                    invert=self.inv_var.get(),sharpness=self.sharp_var.get(),contrast_stretch=self.cs_var.get())
                self.current_image=r; self._push_history(r.copy(),self.method_var.get())
                self.root.after(0,self._update_preview); self._update_status(f"OK - {self.method_var.get()}")
            except Exception as e:
                self.root.after(0,lambda: messagebox.showerror("错误",str(e)))
                self._update_status("出错")
            finally: self.processing=False
        threading.Thread(target=worker,daemon=True).start()

    def _push_history(self,img,name):
        self.history=self.history[:self.history_idx+1]
        self.history.append({"image":img,"name":name,"time":datetime.now().strftime("%H:%M:%S")})
        self.history_idx=len(self.history)-1

    def _undo(self):
        if self.history_idx>0:
            self.history_idx-=1; self.current_image=self.history[self.history_idx]["image"].copy()
            self._update_preview(); self._update_status(f"撤销 -> {self.history[self.history_idx]['name']}")

    def _redo(self):
        if self.history_idx<len(self.history)-1:
            self.history_idx+=1; self.current_image=self.history[self.history_idx]["image"].copy()
            self._update_preview(); self._update_status(f"重做 -> {self.history[self.history_idx]['name']}")

    def _adb_capture(self):
        if not ADB_EXE: return messagebox.showerror("错误","未找到 ADB")
        self._update_status("ADB 截图..."); self.log_frame.grid()
        self._log("ADB 截图...")
        def worker():
            try:
                tmp=os.path.join(tempfile.gettempdir(),"adb_bin_cap.png")
                if not adb_screenshot(tmp):
                    self.root.after(0,lambda: messagebox.showerror("错误","ADB截图失败")); return
                self._log(f"截图 OK: {os.path.getsize(tmp)//1024}KB")
                img=Image.open(tmp).copy()
                try: os.unlink(tmp)
                except: pass
                self.original_image=img; self.original_path=Path("adb_screenshot.png")
                self.current_image=img.copy()
                self.history.clear(); self.history_idx=-1
                self._push_history(img.copy(),"ADB截图")
                self._clear_astar()
                self.root.after(0,self._update_info); self.root.after(0,self._update_preview)
                self.file_lbl.config(text="  ADB截图")
                self.root.after(200,self._process)
            except Exception as e: self._update_status("截图出错"); self._log(f"错误: {e}")
        threading.Thread(target=worker,daemon=True).start()

    def _toggle_astar(self):
        if not self.current_image:
            return messagebox.showinfo("提示","请先处理图片")
        self.astar_mode=not self.astar_mode
        if self.astar_mode:
            self.astar_start=None; self.astar_goal=None; self.astar_path=None; self.astar_overlay=None
            self.astar_btn.config(text="点起点 (点击画布)")
            self.astar_info.config(text="点击设起点 再点设终点",foreground="green")
            self._update_status("A*模式: 在图上点起点")
            self.canvas.config(cursor="target")
        else:
            self._clear_astar()
            self.canvas.config(cursor="crosshair")

    def _clear_astar(self):
        self.astar_mode=False; self.astar_start=None; self.astar_goal=None; self.astar_path=None; self.astar_overlay=None
        self.astar_btn.config(text="点我设起点"); self.astar_info.config(text="关闭",foreground="gray")
        self.canvas.config(cursor="crosshair")
        if self.current_image: self._update_preview()

    # ── 编辑模式 ─────────────────────────────────────────────

    def _toggle_edit(self):
        if not self.current_image:
            return messagebox.showinfo("提示","请先加载并处理图片")
        self.edit_mode=not self.edit_mode
        if self.edit_mode:
            self.astar_mode=False
            self.astar_btn.config(text="点我设起点")
            self.astar_info.config(text="关闭",foreground="gray")
            self.edit_btn.config(text="✏关编辑")
            self.canvas.config(cursor="pencil")
            # 编辑时自动切到结果视图
            self.view_var.set("result")
        else:
            self.edit_btn.config(text="✏编辑")
            self.canvas.config(cursor="crosshair")
        self._update_preview()

    def _edit_pixel(self, px, py):
        if not self.current_image or px<0 or py<0: return
        w,h=self.current_image.size
        if px>=w or py>=h: return
        val = 255 if self.edit_color_var.get()=="white" else 0
        arr = np.array(self.current_image, dtype=np.uint8)
        br = self.brush_var.get()
        y1=max(0,py-br); y2=min(h,py+br+1)
        x1=max(0,px-br); x2=min(w,px+br+1)
        if arr.ndim == 2:
            arr[y1:y2, x1:x2] = val
        else:
            arr[y1:y2, x1:x2] = (val,val,val) if val==255 else (0,0,0)
        self.current_image = Image.fromarray(arr, mode="L" if arr.ndim==2 else "RGB")
        self._clear_astar()

    def _edit_paint(self, e):
        cx=self.canvas.canvasx(e.x); cy=self.canvas.canvasy(e.y)
        z=self.zoom_factor
        cw=max(self.canvas.winfo_width(),100); ch=max(self.canvas.winfo_height(),100)
        img_w=self.current_image.width; img_h=self.current_image.height
        ox=int((cw - img_w*z)/2) if img_w*z < cw else 0
        oy=int((ch - img_h*z)/2) if img_h*z < ch else 0
        px=int((cx - ox)/z); py=int((cy - oy)/z)
        if px<0 or px>=img_w or py<0 or py>=img_h: return
        self._edit_pixel(px, py)
        self._update_preview()

    def _simulate_walk(self):
        """通过ADB模拟摇杆行走沿A*路径"""
        if not self.astar_path or len(self.astar_path) < 2:
            self._update_status("请先计算A*路径（至少2个点）"); return
        if not ADB_EXE:
            self._update_status("未找到ADB"); return
        self.log_frame.grid()
        self._log("=== 模拟行走 ===")
        self._update_status("模拟行走中...")
        self.sim_btn.config(state="disabled")

        def worker():
            try:
                path = self.astar_path
                jx, jy = self.jx_var.get(), self.jy_var.get()
                # 采样路径：每5步取一个点，减少操作次数
                step = max(1, len(path) // 20)  # 最多约20步
                sampled = [path[i] for i in range(0, len(path), step)]
                if sampled[-1] != path[-1]: sampled.append(path[-1])

                # 拖拽距离→速度映射（之前校准过的）
                # 60px≈慢走，120px≈奔跑
                def dist_to_speed(px):
                    if px < 40: return 200, 0.3   # 微调，200ms
                    if px < 80: return 400, 0.6   # 慢走
                    return 600, 1.0                # 奔跑

                adb = [ADB_EXE, "shell"]

                for i in range(1, len(sampled)):
                    x0, y0 = sampled[i-1]
                    x1, y1 = sampled[i]
                    dx, dy = x1 - x0, y1 - y0
                    # 方向：从摇杆中心往目标方向拖
                    angle = np.arctan2(dx, dy)
                    drag_len = min(np.sqrt(dx*dx + dy*dy), 120)  # 不超过奔跑
                    ms, _ = dist_to_speed(drag_len)
                    end_x = int(jx + drag_len * np.sin(angle))
                    end_y = int(jy - drag_len * np.cos(angle))
                    # ADB swipe 模拟摇杆拖拽
                    subprocess.run(adb + [f"input swipe {jx} {jy} {end_x} {end_y} {ms}"],
                                   capture_output=True, timeout=5)
                    # 松开后等一会儿再下一步
                    subprocess.run(adb + [f"input swipe {end_x} {end_y} {jx} {jy} 50"],
                                   capture_output=True, timeout=5)
                    if i % 5 == 0:
                        self._log(f"  已走 {i}/{len(sampled)} 步")

                self._log(f"模拟完成: {len(sampled)} 步")
                self._update_status("模拟行走完成 ✓")
            except Exception as e:
                self._log(f"模拟行走出错: {e}")
                self._update_status("模拟出错")
            finally:
                self.root.after(0, lambda: self.sim_btn.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _canvas_click(self,e):
        if not self.current_image: return
        if self.edit_mode:
            # 编辑涂抹模式
            self._edit_paint(e)
            return
        if not self.astar_mode:  # 普通拖拽
            self._drag_data["x"]=e.x; self._drag_data["y"]=e.y
            return

        # 用 canvasx/canvasy 获取正确的画布物理坐标（含滚动偏移）
        cx=self.canvas.canvasx(e.x); cy=self.canvas.canvasy(e.y)
        # 像素坐标：居中显示，需反算
        z=self.zoom_factor
        cw=max(self.canvas.winfo_width(),100)
        ch=max(self.canvas.winfo_height(),100)
        img_w=self.current_image.width; img_h=self.current_image.height
        # 图片在画布中的左上角坐标（居中）
        ox=int((cw - img_w*z)/2) if img_w*z < cw else 0
        oy=int((ch - img_h*z)/2) if img_h*z < ch else 0
        px=int((cx - ox)/z)
        py=int((cy - oy)/z)
        # 滚动时 ox/oy 可能为负（图片超出画布向左上偏移），无需特殊处理
        if px<0 or px>=img_w or py<0 or py>=img_h: return

        # 调试：查看点击位置的像素值
        arr = np.array(self.current_image.convert("L"), dtype=np.uint8)
        pixel_val = arr[py, px]
        self._update_status(f"点击({px},{py}) 像素值={pixel_val} {'白' if pixel_val >= 128 else '黑'}")

        click = (px, py)

        if self.astar_start is None:
            self.astar_start = click
            self.astar_goal = None
            self.astar_path = None
            self.astar_overlay = None
            self.astar_info.config(text=f"起点({px},{py}) - 再点设终点")
            self._update_status(f"A*起点: ({px},{py})")
            self._draw_astar_markers()
        elif self.astar_goal is None:
            self.astar_goal = click
            self.astar_info.config(text=f"起点({self.astar_start[0]},{self.astar_start[1]}) -> 终点({px},{py})")
            self._update_status(f"A*: 计算路径中...")
            self._run_astar()
        else:
            # 重新设起点
            self.astar_start = click
            self.astar_goal = None
            self.astar_path = None
            self.astar_overlay = None
            self.astar_info.config(text=f"起点({px},{py}) - 再点设终点")
            self._update_status(f"A*起点: ({px},{py})")
            self._draw_astar_markers()

    def _run_astar(self):
        if not self.current_image or not self.astar_start or not self.astar_goal:
            return

        def worker():
            try:
                # 先按用户设置跑，若失败再试无对角线
                diag = self.ad_var.get()
                path = Binarizer.astar(self.current_image, self.astar_start, self.astar_goal,
                                       allow_diagonal=diag)
                if (path is None) and diag:
                    # 有对角线不行，试无对角线
                    path2 = Binarizer.astar(self.current_image, self.astar_start, self.astar_goal,
                                            allow_diagonal=False)
                    if path2 and path2 != "blocked_s" and path2 != "blocked_g":
                        path = path2
                        self._log("A*: 关对角线后路径可用")

                if path and path != "blocked_s" and path != "blocked_g":
                    self.astar_path = path
                    self.astar_overlay = Binarizer.draw_path(self.current_image, path, line_width=3)
                    self._log(f"A*: 找到路径 {len(path)} 步")
                    self._update_status(f"A*: {len(path)} 步路径 ✓")
                else:
                    self.astar_path = None
                    self.astar_overlay = None
                    if path == "blocked_s":
                        msg = "起点在障碍物(黑色)上，请点到白色区域"
                    elif path == "blocked_g":
                        msg = "终点在障碍物(黑色)上，请点到白色区域"
                    else:
                        msg = "无可行路径，起点和终点被障碍隔开了"
                    self._log(f"A*: {msg}")
                    self._update_status(f"A*: {msg}")
                self.root.after(0, self._update_preview)
            except Exception as e:
                self._log(f"A*出错: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def _draw_astar_markers(self):
        """在画布上画起点/终点标记（不跑寻路）"""
        if not self.current_image: return
        self._update_preview()
        # 直接用 _update_preview 显示当前图（由 _get_display_image 处理叠加）

    def _get_display_image(self):
        """获取要显示的图（考虑 A* 叠加 / 并排对比）"""
        mode = self.view_var.get()
        # A*模式下始终显示结果视图（因为寻路只在二值图上才有意义）
        if self.astar_mode or self.astar_overlay is not None or self.astar_start is not None:
            base = self.current_image
            # 有寻路结果时显示彩色叠加图
            if self.astar_overlay is not None:
                return self.astar_overlay
            # 仅在画标记时用
            if self.astar_start or self.astar_goal:
                img = base.convert("RGB") if base.mode != "RGB" else base.copy()
                draw = ImageDraw.Draw(img)
                r = 6
                if self.astar_start:
                    sx, sy = self.astar_start
                    draw.ellipse([sx-r, sy-r, sx+r, sy+r], fill=(0, 255, 0))
                    draw.text((sx+r+2, sy-6), "S", fill=(0, 255, 0))
                if self.astar_goal:
                    gx, gy = self.astar_goal
                    draw.ellipse([gx-r, gy-r, gx+r, gy+r], fill=(255, 0, 0))
                    draw.text((gx+r+2, gy-6), "E", fill=(255, 0, 0))
                return img
            return base
        # 非A*模式：按视图选择
        if mode == "side":
            return self._side_by_side()
        base = self.original_image if mode == "original" else self.current_image
        return base

    def _on_view_change(self):
        """视图切换时不干涉A*状态"""
        self._update_preview()

    def _update_preview(self):
        if not self.current_image:
            self.canvas.delete("all")
            w=max(self.canvas.winfo_width(),100); h=max(self.canvas.winfo_height(),100)
            self.canvas.create_text(w//2,h//2,text="请打开图片",fill="#888",font=("微软雅黑",14))
            return

        img = self._get_display_image()
        if img is None: return

        cw=max(self.canvas.winfo_width(),100); ch=max(self.canvas.winfo_height(),100)
        mode = self.view_var.get()
        if mode != "side":
            self.zoom_factor = min(self.zoom_factor, min(cw/img.width, ch/img.height, 10.0))

        z=self.zoom_factor
        w2=max(int(img.width*z),1); h2=max(int(img.height*z),1)
        self._preview_tk=ImageTk.PhotoImage(img.resize((w2,h2),Image.LANCZOS))
        self.canvas.delete("all")
        self.canvas.create_image(cw//2,ch//2,image=self._preview_tk,anchor="center")
        self.canvas.configure(scrollregion=(-cw//2,-ch//2,cw//2+w2,ch//2+h2))
        self.zlbl.config(text=f"{int(z*100)}%")

    def _side_by_side(self):
        if not self.original_image or not self.current_image: return None
        # 左：原图（转RGB），右：二值结果（也转RGB显示）
        left = self.original_image.convert("RGB")
        right = self.current_image.convert("RGB")
        w=left.width+right.width+4
        h=max(left.height,right.height)
        c=Image.new("RGB",(w,h),(180,180,180))
        c.paste(left,(0,0))
        c.paste(right,(left.width+4,0))
        # 中间分割线
        for y in range(h): c.putpixel((left.width+2,y),(80,80,80))
        return c

    def _zoom_in(self): self.zoom_factor=min(self.zoom_factor*1.3,10.0); self._update_preview()
    def _zoom_out(self): self.zoom_factor=max(self.zoom_factor/1.3,0.05); self._update_preview()
    def _zoom_fit(self):
        if not self.current_image: return
        cw=max(self.canvas.winfo_width(),100); ch=max(self.canvas.winfo_height(),100)
        self.zoom_factor=min(cw/self.current_image.width,ch/self.current_image.height)
        self._update_preview()
    def _zoom_actual(self): self.zoom_factor=1.0; self._update_preview()

    def _drag_move(self,e):
        if self.edit_mode:
            self._edit_paint(e)
            return
        self.canvas.xview_scroll(self._drag_data["x"]-e.x,"units")
        self.canvas.yview_scroll(self._drag_data["y"]-e.y,"units")
        self._drag_data["x"]=e.x; self._drag_data["y"]=e.y

    def _scroll(self,e):
        if e.delta>0: self._zoom_in()
        else: self._zoom_out()


def main():
    root=tk.Tk()
    BinarizerApp(root)
    root.mainloop()

if __name__=="__main__":
    main()
