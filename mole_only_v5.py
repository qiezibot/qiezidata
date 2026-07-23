# -*- coding: utf-8 -*-
import cv2
import numpy as np

img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]
print("Image: {}x{}".format(w, h))

result = img.copy()

# Face detection
net = cv2.dnn.readNetFromCaffe(
    r"C:\u-claw\portable\data\.openclaw\workspace\deploy.prototxt",
    r"C:\u-claw\portable\data\.openclaw\workspace\res10_300x300_ssd_iter_140000.caffemodel"
)
blob = cv2.dnn.blobFromImage(cv2.resize(img, (300,300)), 1.0, (300,300), (104,177,123))
net.setInput(blob)
dets = net.forward()

boxes = []
for i in range(dets.shape[2]):
    conf = dets[0,0,i,2]
    if conf > 0.7:
        box = dets[0,0,i,3:7] * np.array([w,h,w,h])
        fx, fy, fx2, fy2 = box.astype("int")
        cx, cy = (fx+fx2)//2, (fy+fy2)//2
        fs = max(fx2-fx, fy2-fy)
        margin = int(fs * 0.4)
        x1 = max(0, cx - fs//2 - margin)
        y1 = max(0, cy - fs//2 - margin)
        x2 = min(w, cx + fs//2 + margin)
        y2 = min(h, cy + fs//2 + margin)
        boxes.append((x1,y1,x2,y2))

for (x1,y1,x2,y2) in boxes:
    face = img[y1:y2, x1:x2].copy()
    fh, fw = face.shape[:2]
    
    # Key insight: a mole is a dark, roughly circular spot
    # We want to replace ONLY the mole pixels, nothing else
    
    # LAB for better color analysis
    lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
    l, a_chan, b_chan = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(15,15))
    l_eq = clahe.apply(l)
    
    # Top-hat to isolate small dark spots
    ksize = 51
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    bh = cv2.morphologyEx(l_eq, cv2.MORPH_BLACKHAT, kernel)
    
    # Threshold to find spots
    _, spots = cv2.threshold(bh, 20, 255, cv2.THRESH_BINARY)
    
    # Find connected components
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(spots, 8)
    
    # Create a spot mask
    spot_mask = np.zeros((fh, fw), dtype=np.uint8)
    found_spots = 0
    
    for j in range(1, n_labels):
        area = stats[j, cv2.CC_STAT_AREA]
        sx, sy, sw, sh = stats[j, cv2.CC_STAT_LEFT], stats[j, cv2.CC_STAT_TOP], stats[j, cv2.CC_STAT_WIDTH], stats[j, cv2.CC_STAT_HEIGHT]
        
        # Size range for moles
        if area < 20 or area > 400:
            continue
        
        # Circularity
        pts = np.array([[sx, sy], [sx+sw, sy], [sx+sw, sy+sh], [sx, sy+sh]], dtype=np.float32)
        peri = cv2.arcLength(pts, True)
        circ = 4 * np.pi * area / (peri * peri) if peri > 0 else 0
        
        aspect = max(sw, sh) / max(1, min(sw, sh))
        
        if circ > 0.2 and aspect < 2.5:
            # Check darkness
            roi_l = l_eq[sy:sy+sh, sx:sx+sw]
            mean_dark = np.mean(roi_l)
            
            local_y1 = max(0, sy-20)
            local_y2 = min(fh, sy+sh+20)
            local_x1 = max(0, sx-20)
            local_x2 = min(fw, sx+sw+20)
            local = l_eq[local_y1:local_y2, local_x1:local_x2]
            local_mean = np.mean(local)
            
            if local_mean - mean_dark > 8:  # Significantly darker than surroundings
                spot_mask[labels == j] = 255
                found_spots += 1
                print("  Spot {}: abs=({},{}), area={}, circ={:.2f}".format(
                    found_spots, sx+x1, sy+y1, area, circ))
    
    if found_spots > 0:
        # CRITICAL: Only inpaint the mole pixels, not dilate too much
        # Dilate just a tiny bit for smooth transition
        kernel_small = np.ones((3,3), np.uint8)
        mask_d = cv2.dilate(spot_mask, kernel_small, iterations=1)
        
        # Inpaint with TELEA (preserves texture)
        inpainted = cv2.inpaint(face, mask_d, 2, cv2.INPAINT_TELEA)
        
        # Blend with ORIGINAL face - only replace the spot pixels
        # Use the SPOT mask only, not dilated
        spot_float = spot_mask.astype(np.float32) / 255.0
        
        # Feather edges a tiny bit
        spot_feather = cv2.GaussianBlur(spot_float, (5,5), 1)
        
        # IMPORTANT: blend inpainted into face, keeping ALL original non-spot pixels
        spot_3ch = cv2.merge([spot_feather]*3)
        blended = inpainted.astype(np.float32) * spot_3ch + face.astype(np.float32) * (1 - spot_3ch)
        
        result[y1:y2, x1:x2] = blended.astype(np.uint8)
        print("Treated {} moles, blending preserves original skin tone.".format(found_spots))
    else:
        # Fallback: use even more aggressive but still pixel-level
        print("No spots found with strict criteria, trying relaxed...")
        _, spots2 = cv2.threshold(bh, 15, 255, cv2.THRESH_BINARY)
        n2, labels2, stats2, _ = cv2.connectedComponentsWithStats(spots2, 8)
        mask2 = np.zeros_like(l_eq)
        count2 = 0
        for j in range(1, n2):
            area = stats2[j, cv2.CC_STAT_AREA]
            if 15 < area < 500:
                sx, sy = stats2[j, cv2.CC_STAT_LEFT], stats2[j, cv2.CC_STAT_TOP]
                sw, sh = stats2[j, cv2.CC_STAT_WIDTH], stats2[j, cv2.CC_STAT_HEIGHT]
                asp = max(sw, sh) / max(1, min(sw, sh))
                if asp < 3:
                    mask2[labels2 == j] = 255
                    count2 += 1
                    print("  Fallback: ({},{}) area={}".format(sx+x1, sy+y1, area))
        if count2 > 0:
            md = cv2.dilate(mask2, np.ones((3,3),np.uint8), 1)
            inp = cv2.inpaint(face, md, 2, cv2.INPAINT_TELEA)
            mf = mask2.astype(np.float32)/255.0
            m_f = cv2.GaussianBlur(mf, (5,5), 1)
            mc = cv2.merge([m_f]*3)
            result[y1:y2, x1:x2] = (inp.astype(np.float32)*mc + face.astype(np.float32)*(1-mc)).astype(np.uint8)
            print("Fallback: treated {} spots".format(count2))

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Done! Skin tone preserved.")
