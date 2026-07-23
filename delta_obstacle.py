"""
三角洲行动 - 障碍物/卡住检测模块
原理：连续截图对比画面相似度，配合深度检测判断是否被墙/石头/建筑物挡住
"""
import subprocess, cv2, numpy as np, time, math

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = '1aabaaeb'

def screencap():
    """获取横屏截图"""
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'],
                       capture_output=True, timeout=10)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is not None and img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

def images_similarity(img1, img2):
    """计算两帧画面相似度（0-1）- 用于检测是否卡住"""
    if img1 is None or img2 is None:
        return 0
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    if h1 != h2 or w1 != w2:
        return 0
    g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    # 缩小到64x64比较
    s1 = cv2.resize(g1, (64, 64))
    s2 = cv2.resize(g2, (64, 64))
    mse = np.mean((s1.astype(float) - s2.astype(float)) ** 2)
    # MSE转相似度：0~255^2范围
    sim = max(0, 1 - mse / 65025)
    return sim

def detect_wall(img):
    """
    检测前方是否有墙/障碍物
    思路：分析画面中心区域是否有大面积同色块（墙壁/山体）
    正常画面：天空+地面+远近层次
    撞墙画面：大面积单一纹理（墙面堵住大部分视野）
    """
    if img is None:
        return False, 0
    
    h, w = img.shape[:2]
    
    # 1. 取画面中间60%区域作为"前方视野"
    cx, cy = w // 2, h // 2
    roi = img[int(cy*0.4):int(cy*1.6), int(cx*0.3):int(cx*1.7)]
    if roi.size == 0:
        return False, 0
    
    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # 2. 计算纹理丰富度（方差）
    laplacian = cv2.Laplacian(roi_gray, cv2.CV_64F)
    texture_var = laplacian.var()
    
    # 3. 检测大面积同色块
    # 转为HSV看色相分布
    roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    h_channel = roi_hsv[:,:,0].flatten()
    
    # 色相直方图（只看有颜色区域，排除黑/白/灰）
    s_channel = roi_hsv[:,:,1]
    colored_indices = s_channel > 30
    colored_h = h_channel[colored_indices.flatten()]
    
    if len(colored_h) > 0:
        # 计算色相集中度
        hist = cv2.calcHist([roi_hsv], [0], None, [180], [0, 180])
        max_hue_pct = hist.max() / hist.sum() if hist.sum() > 0 else 0
    else:
        max_hue_pct = 0
    
    # 4. 边缘检测
    edges = cv2.Canny(roi_gray, 50, 150)
    edge_density = cv2.countNonZero(edges) / (roi.shape[0] * roi.shape[1])
    
    # 判断逻辑
    is_stuck = False
    reason = ""
    
    # 纹理极低 + 边缘少 = 墙壁或天空
    if texture_var < 30 and edge_density < 0.05:
        # 进一步区分墙和天空
        bright = roi_gray.mean()
        if bright < 120:
            is_stuck = True
            reason = f"暗墙(texture={texture_var:.1f}, edge={edge_density:.3f})"
        else:
            reason = f"天空(texture={texture_var:.1f})"
    
    # 单一色相大面积覆盖 = 墙
    if max_hue_pct > 0.3 and texture_var < 50:
        is_stuck = True
        reason = f"单色块(hue_pct={max_hue_pct:.2f}, texture={texture_var:.1f})"
    
    # 画面50%以上是同一颜色且边缘极少
    if texture_var < 20:
        is_stuck = True
        reason = f"无纹理(texture={texture_var:.1f})"
    
    return is_stuck, reason if reason else f"ok(texture={texture_var:.1f}, hue={max_hue_pct:.2f}, edge={edge_density:.3f})"

def find_open_direction(img):
    """
    找视野中最空旷的方向（没有墙）
    返回建议转向角度（左转/右转，以及角度值）
    """
    if img is None:
        return 0
    
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # 将画面分左右两半比较
    mid = w // 2
    left_half = edges[:, :mid]
    right_half = edges[:, mid:]
    
    left_edges = cv2.countNonZero(left_half)
    right_edges = cv2.countNonZero(right_half)
    
    total_edges = left_edges + right_edges
    if total_edges == 0:
        return 0
    
    # 边缘少的一侧 = 更空旷
    ratio = left_edges / total_edges if total_edges > 0 else 0.5
    
    # ratio<0.35=左边空旷(右转看向左), ratio>0.65=右边空旷(左转看向右)
    if ratio < 0.4:
        return -45  # 右转45度看向空旷处（左）
    elif ratio > 0.6:
        return 45   # 左转45度看向空旷处（右）
    else:
        # 上下分
        top_half = edges[:h//2, :]
        bot_half = edges[h//2:, :]
        top_edges = cv2.countNonZero(top_half)
        bot_edges = cv2.countNonZero(bot_half)
        total_ud = top_edges + bot_edges
        if total_ud == 0:
            return 0
        ud_ratio = top_edges / total_ud
        if ud_ratio < 0.4:
            return 135  # 往上看
        elif ud_ratio > 0.6:
            return -135  # 往下看
        return 0

if __name__ == '__main__':
    print("=== 障碍物检测测试 ===")
    img = screencap()
    if img is None:
        print("截图失败")
        exit()
    
    is_stuck, reason = detect_wall(img)
    direction = find_open_direction(img)
    print(f"截图尺寸: {img.shape[1]}x{img.shape[0]}")
    print(f"障碍物: {'✅ 挡住' if is_stuck else '❌ 空旷'}")
    print(f"分析: {reason}")
    print(f"建议转向: {direction}度")
