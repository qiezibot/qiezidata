#!/usr/bin/env python3
"""分析视频内容"""
import cv2, json, os
import numpy as np

VIDEO = r'C:\Users\lfy20\.openclaw\media\qqbot\downloads\1904006743\CC26706F41E5B48C18ADF3C2A2AF86A0\920d9998-db91-4be1-b49c-8fec11e0e7ef.mp4'

cap = cv2.VideoCapture(VIDEO)
fps = cap.get(cv2.CAP_PROP_FPS)
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
dur = total / fps

print(f"== 视频信息 ==")
print(f"时长: {dur:.1f}秒")
print(f"分辨率: 720x1280")
print(f"帧率: {fps:.1f}fps")
print(f"总帧数: {total}")
print()

# 逐关键帧分析
frames_desc = []
prev_gray = None
scene_count = 0

for sec in range(0, int(dur), 2):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(sec * fps))
    ret, frame = cap.read()
    if not ret:
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 检测是否为黑屏/纯色
    black_pixels = (gray < 10).sum() / gray.size
    if black_pixels > 0.8:
        if not frames_desc or frames_desc[-1].get('content') != '黑屏/过渡':
            frames_desc.append({'time': sec, 'content': '黑屏/过渡'})
        continue
    
    # 跳过重复画面（变化太小）
    if prev_gray is not None:
        diff = np.abs(gray.astype(int) - prev_gray.astype(int)).mean()
        if diff < 15:
            continue
    
    prev_gray = gray
    scene_count += 1
    
    # 分析颜色分布
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, w = frame.shape[:2]
    
    # 提取中央区域
    center = frame[h//4:3*h//4, w//4:3*w//4]
    center_hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    
    avg_h = center_hsv[:,:,0].mean()
    avg_s = center_hsv[:,:,1].mean()
    avg_v = center_hsv[:,:,2].mean()
    
    # 人脸检测
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    has_face = len(faces) > 0
    
    # 颜色判断
    if avg_h < 15 or avg_h > 165:
        color_tone = "红色/暖色"
    elif avg_h < 35:
        color_tone = "黄色/橙色"
    elif avg_h < 85:
        color_tone = "绿色(植物/树木)"
    elif avg_h < 130:
        color_tone = "蓝色(天空/水)"
    elif avg_h < 155:
        color_tone = "紫色/粉色"
    else:
        color_tone = "混合色"
    
    # 场景类型推测
    if avg_v > 150 and avg_h > 70 and avg_h < 110:
        scene_type = "户外/天空"
    elif avg_v > 100 and avg_h > 35 and avg_h < 80:
        scene_type = "户外/植被"
    elif avg_v < 80:
        scene_type = "室内/暗光"
    elif avg_s < 30 and avg_v > 100:
        scene_type = "室内/明亮"
    elif has_face:
        scene_type = "人物/自拍"
    else:
        scene_type = "室外自然"
    
    frame_info = {
        'time': sec,
        'content': scene_type,
        'color': color_tone,
        'brightness': f"{'明亮' if avg_v > 120 else '适中' if avg_v > 60 else '偏暗'}",
        'faces': len(faces),
        'motion': '有动作' if avg_s > 50 else '较静态',
        'center_rgb': [int(center[:,:,2].mean()), int(center[:,:,1].mean()), int(center[:,:,0].mean())]
    }
    frames_desc.append(frame_info)
    
    # 保存关键帧预览
    preview = cv2.resize(frame, (360, 640))
    out_path = f'C:\\temp\\pics\\scene_{sec:02d}s.jpg'
    cv2.imwrite(out_path, preview, [cv2.IMWRITE_JPEG_QUALITY, 75])

cap.release()

print(f"== 场景分析 ==")
print(f"检测到 {scene_count} 个有意义画面")
print()

for f in frames_desc:
    face_str = f" 有人脸x{f['faces']}" if f['faces'] > 0 else ""
    print(f"  {f['time']:2d}s | {f['content']:10s} | {f['color']:14s} | 亮度:{f['brightness']:4s}{face_str}")

# 综合结论
contents = [f['content'] for f in frames_desc]
colors_used = [f['color'] for f in frames_desc]
has_people = any(f['faces'] > 0 for f in frames_desc)
outdoor = sum(1 for c in contents if '户外' in c)
indoor = sum(1 for c in contents if '室内' in c)
people = sum(1 for c in contents if '人物' in c)
black = sum(1 for c in contents if '黑屏' in c)

print()
print(f"== 综合结论 ==")
print(f"户外场景: {outdoor}/{scene_count}")
print(f"室内场景: {indoor}/{scene_count}")
print(f"有人出镜: {'是' if has_people else '否'}")
print(f"主要色调: {max(set(colors_used), key=colors_used.count)}")

# 内容类型
if has_people:
    print("视频类型: 人物出镜类（自拍/Vlog）")
elif outdoor > indoor:
    print("视频类型: 户外自然/生活类")
else:
    print("视频类型: 室内场景类")

print()
print("== 热门剪辑建议 ==")
if has_people:
    print("✅ 有真人出镜 → 适合做人物故事/口播类")
    print("建议: 前3秒特写+一句话钩子")
else:
    print("❌ 无人出镜 → 需配旁白/BGM")
    print("建议: 加人物自拍或画外音")
if outdoor > 0:
    print("✅ 户外场景多 → 适合三农/乡村内容")
else:
    print("⚠️ 室内为主 → 适合做饭/手工/生活记录")
