"""Fine mole detection - find the actual prominent mole(s) on the face"""
import cv2
import numpy as np

img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]
print(f"Image size: {w}x{h}")

# Face detection
net = cv2.dnn.readNetFromCaffe(
    r"C:\u-claw\portable\data\.openclaw\workspace\deploy.prototxt",
    r"C:\u-claw\portable\data\.openclaw\workspace\res10_300x300_ssd_iter_140000.caffemodel"
)
blob = cv2.dnn.blobFromImage(cv2.resize(img, (300,300)), 1.0, (300,300), (104,177,123))
net.setInput(blob)
dets = net.forward()

result = img.copy()
debug_small = cv2.resize(img, (0,0), fx=0.25, fy=0.25)

# Use the face from the original image (not CodeFormer processed)
for i in range(dets.shape[2]):
    conf = dets[0,0,i,2]
    if conf > 0.5:
        box = dets[0,0,i,3:7] * np.array([w,h,w,h])
        fx, fy, fx2, fy2 = box.astype("int")
        cx, cy = (fx+fx2)//2, (fy+fy2)//2
        fs = max(fx2-fx, fy2-fy)
        margin = int(fs * 0.5)  # Larger margin
        x1 = max(0, cx - fs//2 - margin)
        y1 = max(0, cy - fs//2 - margin)
        x2 = min(w, cx + fs//2 + margin)
        y2 = min(h, cy + fs//2 + margin)
        
        face = img[y1:y2, x1:x2].copy()
        face_h, face_w = face.shape[:2]
        print(f"Face region: ({x1},{y1})-({x2},{y2}), size={face_w}x{face_h}")
        
        # Strategy: Look for the MOST prominent dark spots
        # At 4284x5712, a real mole should be ~40-200 px
        
        # 1. LAB color space - L channel
        lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # 2. CLAHE normalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(15,15))
        l_eq = clahe.apply(l)
        
        # 3. Blackhat to find dark spots on light background
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51))
        bh = cv2.morphologyEx(l_eq, cv2.MORPH_BLACKHAT, kernel)
        
        # 4. Multiple thresholds
        # Try threshold to find significant moles only
        for thresh_val in [15, 20, 25, 30, 35, 40, 45, 50]:
            _, mask = cv2.threshold(bh, thresh_val, 255, cv2.THRESH_BINARY)
            n_labels, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
            large_spots = [stats[j] for j in range(1, n_labels) if 100 < stats[j,cv2.CC_STAT_AREA] < 600]
            if len(large_spots) >= 1:
                print(f"Threshold {thresh_val}: found {len(large_spots)} significant spots")
                break
        else:
            print("No significant spots at any threshold")
            # Fallback: find ANY dark spot
            _, mask = cv2.threshold(bh, 10, 255, cv2.THRESH_BINARY)
        
        # 5. Analyze components - find moles vs noise
        n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
        print(f"Total components: {n_labels - 1}")
        
        mole_mask = np.zeros_like(l_eq)
        moles_info = []
        
        for j in range(1, n_labels):
            area = stats[j, cv2.CC_STAT_AREA]
            sx, sy, sw, sh = stats[j, cv2.CC_STAT_LEFT], stats[j, cv2.CC_STAT_TOP], stats[j, cv2.CC_STAT_WIDTH], stats[j, cv2.CC_STAT_HEIGHT]
            
            # Reasonable mole size at this resolution
            if area < 30 or area > 500:
                continue
            
            # Circularity
            perimeter = cv2.arcLength(
                np.array([[sx, sy], [sx+sw, sy], [sx+sw, sy+sh], [sx, sy+sh]], dtype=np.float32), True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            
            # Aspect ratio
            aspect = max(sw, sh) / max(1, min(sw, sh))
            
            # Get the dark area
            roi_l = l_eq[sy:sy+sh, sx:sx+sw]
            mean_dark = np.mean(roi_l)
            
            # Local surroundings
            y_start_pad = max(0, sy - min(30, sy))
            y_end_pad = min(l_eq.shape[0], sy + sh + min(30, l_eq.shape[0]-sy-sh))
            x_start_pad = max(0, sx - min(30, sx))
            x_end_pad = min(l_eq.shape[1], sx + sw + min(30, l_eq.shape[1]-sx-sw))
            local = l_eq[y_start_pad:y_end_pad, x_start_pad:x_end_pad]
            local_mean = np.mean(local)
            
            contrast = local_mean - mean_dark
            
            # A real mole is circular-ish, darker than surroundings
            if circularity > 0.25 and aspect < 2.5 and contrast > 8:
                mole_mask[labels == j] = 255
                moles_info.append({
                    'abs_x': sx + x1,
                    'abs_y': sy + y1,
                    'w': sw, 'h': sh,
                    'area': area,
                    'circ': circularity,
                    'contrast': contrast
                })
                print(f"  Mole #{len(moles_info)}: abs=({sx+x1},{sy+y1}), size={sw}x{sh}, area={area}, circ={circularity:.2f}, contrast={contrast:.1f}")
        
        if moles_info:
            # Apply inpainting
            kernel_d = np.ones((9,9), np.uint8)
            mask_d = cv2.dilate(mole_mask, kernel_d, iterations=1)
            mask_f = cv2.GaussianBlur(mask_d.astype(np.float32), (7,7), 0)
            mask_f = np.clip(mask_f, 0, 255).astype(np.uint8)
            
            inpainted = cv2.inpaint(face, mask_f, 3, cv2.INPAINT_TELEA)
            
            # Blend with original face
            m_float = mask_f.astype(np.float32) / 255.0
            m_3ch = cv2.merge([m_float]*3)
            blended = inpainted.astype(np.float32) * m_3ch + face.astype(np.float32) * (1 - m_3ch)
            result[y1:y2, x1:x2] = blended.astype(np.uint8)
            print(f"✅ Inpainted {len(moles_info)} moles")
        else:
            print("❌ No moles found with current criteria, relaxing...")
            # Relax all criteria
            for j in range(1, n_labels):
                area = stats[j, cv2.CC_STAT_AREA]
                if area < 20 or area > 600:
                    continue
                mole_mask[labels == j] = 255
                sx, sy = stats[j, cv2.CC_STAT_LEFT], stats[j, cv2.CC_STAT_TOP]
                sw, sh = stats[j, cv2.CC_STAT_WIDTH], stats[j, cv2.CC_STAT_HEIGHT]
                print(f"  Relaxed: ({sx+x1},{sy+y1}) area={area}")
            
            if cv2.countNonZero(mole_mask) > 0:
                md = cv2.dilate(mole_mask, np.ones((9,9),np.uint8), 1)
                mf = cv2.GaussianBlur(md.astype(np.float32), (7,7), 0)
                mf = np.clip(mf, 0, 255).astype(np.uint8)
                inp = cv2.inpaint(face, mf, 3, cv2.INPAINT_TELEA)
                mf3 = cv2.merge([mf.astype(np.float32)/255.0]*3)
                result[y1:y2, x1:x2] = (inp.astype(np.float32)*mf3 + face.astype(np.float32)*(1-mf3)).astype(np.uint8)
                print("✅ Relaxed inpaint done")
            else:
                print("❌ No spots at all")
                result = img.copy()

# Save
cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
print("Done!")
