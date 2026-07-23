use std::path::PathBuf;
use std::fs;
use image::{GrayImage, Luma};
use clap::Parser;
use serde::Deserialize;
use anyhow::{Result, Context};

/// 图片二值化工具 — 支持多种算法和批量处理
#[derive(Parser, Debug)]
#[command(name = "binarizer", version, about)]
struct Args {
    /// 输入图片路径（支持 * ? glob 通配符）
    #[arg(short, long)]
    input: Vec<String>,

    /// 输入目录（处理目录下所有图片）
    #[arg(short = 'd', long)]
    input_dir: Option<PathBuf>,

    /// 输出目录（默认覆盖输入）
    #[arg(short = 'o', long)]
    output_dir: Option<PathBuf>,

    /// 输出后缀（默认 _bin.png）
    #[arg(short = 's', long, default_value = "_bin")]
    suffix: String,

    /// 二值化方法（全局/自适应/otsu/triangle/intermodes/entropy/minerror）
    #[arg(short = 'M', long, default_value = "otsu")]
    method: String,

    /// 全局阈值（0-255），仅 method=global 时有效
    #[arg(short = 't', long)]
    threshold: Option<u8>,

    /// 自适应窗口大小（奇数，默认 31），仅 method=adaptive 时有效
    #[arg(short = 'w', long, default_value = "31")]
    window: u32,

    /// 自适应常数 C
    #[arg(short = 'c', long, default_value = "10")]
    c: i32,

    /// 先高斯模糊去除噪点（0=不模糊）
    #[arg(short = 'b', long, default_value = "0")]
    blur: f64,

    /// 预处理：灰度直方图均衡化
    #[arg(short = 'e', long)]
    equalize: bool,

    /// 预处理：CLAHE 增强对比度 (窗口大小，默认 64)
    #[arg(long)]
    clahe: Option<u32>,

    /// 输出格式：png / jpg / bmp / webp
    #[arg(short = 'f', long, default_value = "png")]
    format: String,

    /// 是否反转（白变黑，黑变白）
    #[arg(short = 'i', long)]
    invert: bool,

    /// PNG 压缩级别（0-9，默认 6）
    #[arg(long, default_value = "6")]
    png_compression: u8,

    /// 显示调试信息
    #[arg(short = 'v', long)]
    verbose: bool,

    /// 打开 GUI 界面
    #[arg(long)]
    gui: bool,

    /// 配置文件路径（json）
    #[arg(short = 'C', long)]
    config: Option<PathBuf>,
}

#[derive(Deserialize, Default)]
struct Config {
    input: Option<Vec<String>>,
    input_dir: Option<PathBuf>,
    output_dir: Option<PathBuf>,
    suffix: Option<String>,
    method: Option<String>,
    threshold: Option<u8>,
    window: Option<u32>,
    c: Option<i32>,
    blur: Option<f64>,
    equalize: Option<bool>,
    clahe: Option<u32>,
    format: Option<String>,
    invert: Option<bool>,
    png_compression: Option<u8>,
    verbose: Option<bool>,
}

/// 直方图
struct Histogram {
    data: [u32; 256],
    total: u32,
}

impl Histogram {
    fn from_gray(img: &GrayImage) -> Self {
        let mut data = [0u32; 256];
        for p in img.pixels() {
            data[p.0[0] as usize] += 1;
        }
        let total = img.width() * img.height();
        Histogram { data, total }
    }

    /// Otsu 阈值
    fn otsu_threshold(&self) -> u8 {
        let total = self.total as f64;
        let mut max_var = 0f64;
        let mut best = 0u8;

        for t in 1..255 {
            let w1 = self.data[..=t].iter().sum::<u32>() as f64;
            let w2 = total - w1;
            if w1 < 1.0 || w2 < 1.0 {
                continue;
            }
            let m1: f64 = self.data[..=t]
                .iter()
                .enumerate()
                .map(|(i, &c)| (i as f64) * (c as f64))
                .sum::<f64>() / w1;
            let m2: f64 = self.data[t + 1..]
                .iter()
                .enumerate()
                .map(|(i, &c)| ((i + t + 1) as f64) * (c as f64))
                .sum::<f64>() / w2;
            let var = w1 * w2 * (m1 - m2).powi(2);
            if var > max_var {
                max_var = var;
                best = t as u8;
            }
        }
        best
    }

    /// Triangle 阈值法（基于 Zack & Rogers）
    fn triangle_threshold(&self) -> u8 {
        // 找到直方图最高峰
        let mut peak_idx = 0u8;
        let mut peak_val = 0u32;
        for (i, &v) in self.data.iter().enumerate() {
            if v > peak_val {
                peak_val = v;
                peak_idx = i as u8;
            }
        }

        // 找到左侧和右侧的边界（非零的最远端）
        let mut left_min = 0u8;
        let mut right_max = 255u8;
        for i in 0..256 {
            if self.data[i] > 0 { left_min = i as u8; break; }
        }
        for i in (0..256).rev() {
            if self.data[i] > 0 { right_max = i as u8; break; }
        }

        // 确定距离峰值更远的端点
        let (x1, y1) = if (peak_idx as i16 - left_min as i16).abs() >= (peak_idx as i16 - right_max as i16).abs() {
            (left_min, 0i64)
        } else {
            (right_max, 0i64)
        };

        let (x2, y2) = (peak_idx, peak_val as i64);
        let dx = x2 as i64 - x1 as i64;
        let dy = y2 - y1;

        let mut max_dist = 0i64;
        let mut best = 0u8;

        let range: Box<dyn Iterator<Item = i64>> = if x2 >= x1 {
            Box::new(x1 as i64..=x2 as i64)
        } else {
            Box::new(x2 as i64..=x1 as i64)
        };

        for x in range {
            let y = self.data[x as usize] as i64;
            let dist = ((dy * x - dx * y + x2 * y1 - y2 * x1) as i64).abs();
            if dist > max_dist {
                max_dist = dist;
                best = x as u8;
            }
        }
        best
    }

    /// Intermodes 法：双峰之间的中点
    fn intermodes_threshold(&self) -> u8 {
        // 用卷积平滑直方图
        let smoothed = self.smooth_histogram(5);
        // 找局部极大值
        let peaks = find_peaks(&smoothed);
        if peaks.len() >= 2 {
            let p1 = peaks[0];
            let p2 = peaks[peaks.len() - 1];
            ((p1 + p2) / 2) as u8
        } else {
            self.otsu_threshold()
        }
    }

    /// Kapur 熵阈值法
    fn entropy_threshold(&self) -> u8 {
        let total = self.total as f64;
        let mut max_entropy = 0f64;
        let mut best = 0u8;

        for t in 1..255 {
            let sum_bg = self.data[..=t].iter().sum::<u32>() as f64;
            let sum_fg = total - sum_bg;
            if sum_bg < 1.0 || sum_fg < 1.0 { continue; }

            let h_bg: f64 = self.data[..=t].iter()
                .filter(|&&v| v > 0)
                .map(|&v| { let p = v as f64 / sum_bg; -p * p.log2() })
                .sum();
            let h_fg: f64 = self.data[t+1..].iter()
                .filter(|&&v| v > 0)
                .map(|&v| { let p = v as f64 / sum_fg; -p * p.log2() })
                .sum();

            let total_entropy = h_bg + h_fg;
            if total_entropy > max_entropy {
                max_entropy = total_entropy;
                best = t as u8;
            }
        }
        best
    }

    /// Minimum Error 法（Kittler & Illingworth）
    fn min_error_threshold(&self) -> u8 {
        let total = self.total as f64;
        let mut min_err = f64::MAX;
        let mut best = 0u8;

        for t in 1..255 {
            let sum_bg = self.data[..=t].iter().sum::<u32>() as f64;
            let sum_fg = total - sum_bg;
            if sum_bg < 1.0 || sum_fg < 1.0 { continue; }

            let mean_bg: f64 = self.data[..=t].iter().enumerate()
                .map(|(i, &c)| (i as f64) * (c as f64)).sum::<f64>() / sum_bg;
            let var_bg: f64 = self.data[..=t].iter().enumerate()
                .map(|(i, &c)| ((i as f64) - mean_bg).powi(2) * (c as f64)).sum::<f64>() / sum_bg;
            let mean_fg: f64 = self.data[t+1..].iter().enumerate()
                .map(|(i, &c)| ((i + t + 1) as f64) * (c as f64)).sum::<f64>() / sum_fg;
            let var_fg: f64 = self.data[t+1..].iter().enumerate()
                .map(|(i, &c)| ((i + t + 1) as f64 - mean_fg).powi(2) * (c as f64)).sum::<f64>() / sum_fg;

            if var_bg < 1e-6 || var_fg < 1e-6 { continue; }

            let j = 1.0 + 2.0 * (sum_bg / total * var_bg.ln() + sum_fg / total * var_fg.ln())
                - 2.0 * (sum_bg / total * (mean_bg - mean_fg) + sum_fg / total * (mean_fg - mean_bg));
            if j < min_err {
                min_err = j;
                best = t as u8;
            }
        }
        best
    }

    fn smooth_histogram(&self, passes: usize) -> Vec<u32> {
        let mut h = self.data.to_vec();
        for _ in 0..passes {
            let mut smoothed = vec![0u32; 256];
            for i in 1..255 {
                smoothed[i] = (h[i-1] + h[i] * 2 + h[i+1]) / 4;
            }
            smoothed[0] = h[0];
            smoothed[255] = h[255];
            h = smoothed;
        }
        h
    }
}

fn find_peaks(hist: &[u32]) -> Vec<u8> {
    let mut peaks = Vec::new();
    for i in 1..255 {
        if hist[i] > hist[i-1] && hist[i] >= hist[i+1] {
            peaks.push(i as u8);
        }
    }
    peaks
}

/// 全局阈值二值化
fn global_threshold(img: &GrayImage, threshold: u8) -> GrayImage {
    let (w, h) = img.dimensions();
    GrayImage::from_fn(w, h, |x, y| {
        let p = img.get_pixel(x, y).0[0];
        if p > threshold { Luma([255]) } else { Luma([0]) }
    })
}

/// 自适应局部阈值（Sauvola-style）
fn adaptive_threshold(img: &GrayImage, window: u32, c: i32) -> GrayImage {
    let (w, h) = img.dimensions();
    let half = (window / 2) as i64;
    let mut out = GrayImage::new(w, h);

    // 积分图和平方和积分图
    let mut integral = vec![0i64; ((w+1) * (h+1)) as usize];
    let mut integral_sq = vec![i64; ((w+1) * (h+1)) as usize];
    let stride = (w + 1) as usize;

    for y in 0..h {
        for x in 0..w {
            let p = img.get_pixel(x, y).0[0] as i64;
            let idx = ((y+1) * (w+1) + (x+1)) as usize;
            integral[idx] = p + integral[idx - 1] + integral[(y as usize) * stride + (x+1) as usize] - integral[(y as usize) * stride + x as usize];
            integral_sq[idx] = p*p + integral_sq[idx - 1] + integral_sq[(y as usize) * stride + (x+1) as usize] - integral_sq[(y as usize) * stride + x as usize];
        }
    }

    for y in 0..h {
        for x in 0..w {
            let x1 = (x as i64 - half).max(0) as u32;
            let y1 = (y as i64 - half).max(0) as u32;
            let x2 = (x as i64 + half).min((w-1) as i64) as u32;
            let y2 = (y as i64 + half).min((h-1) as i64) as u32;

            let area = ((x2 - x1 + 1) * (y2 - y1 + 1)) as i64;

            let idx_sum = |x: u32, y: u32| -> usize { (y * (w+1) + x) as usize };

            let sum = integral[idx_sum(x2+1, y2+1)]
                - integral[idx_sum(x1, y2+1)]
                - integral[idx_sum(x2+1, y1)]
                + integral[idx_sum(x1, y1)];

            let sum_sq = integral_sq[idx_sum(x2+1, y2+1)]
                - integral_sq[idx_sum(x1, y2+1)]
                - integral_sq[idx_sum(x2+1, y1)]
                + integral_sq[idx_sum(x1, y1)];

            let mean = sum / area;
            let variance = sum_sq / area - mean * mean;
            let std_dev = (variance as f64).sqrt() as i64;

            let p = img.get_pixel(x, y).0[0] as i64;
            let threshold = mean - c as i64;
            // Sauvola: mean * (1 + 0.2 * (std_dev/128 - 1)) — 简化用 mean - C
            out.put_pixel(x, y, if p > threshold { Luma([255]) } else { Luma([0]) });
        }
    }
    out
}

/// 高斯模糊
fn gaussian_blur(img: &GrayImage, sigma: f64) -> GrayImage {
    image::imageops::blur(img, sigma)
}

/// 直方图均衡化
fn histogram_equalize(img: &GrayImage) -> GrayImage {
    let mut out = img.clone();
    let hist = Histogram::from_gray(img);
    let total = hist.total as f64;

    // 计算 CDF
    let mut cdf = [0u32; 256];
    cdf[0] = hist.data[0];
    for i in 1..256 {
        cdf[i] = cdf[i-1] + hist.data[i];
    }

    // 找到最小非零 CDF
    let cdf_min = cdf.iter().find(|&&v| v > 0).copied().unwrap_or(0);

    for y in 0..img.height() {
        for x in 0..img.width() {
            let p = img.get_pixel(x, y).0[0];
            let v = ((cdf[p as usize] - cdf_min) as f64 / (total - cdf_min as f64) * 255.0).round() as u8;
            out.put_pixel(x, y, Luma([v]));
        }
    }
    out
}

/// CLAHE（对比度受限自适应直方图均衡化）
fn clahe(img: &GrayImage, tile_size: u32, clip_limit: u8) -> GrayImage {
    let (w, h) = img.dimensions();
    let tiles_x = ((w as f64) / tile_size as f64).ceil() as u32;
    let tiles_y = ((h as f64) / tile_size as f64).ceil() as u32;

    let mut out = GrayImage::new(w, h);

    for ty in 0..tiles_y {
        for tx in 0..tiles_x {
            let x0 = tx * tile_size;
            let y0 = ty * tile_size;
            let x1 = (x0 + tile_size - 1).min(w - 1);
            let y1 = (y0 + tile_size - 1).min(h - 1);

            // 统计局部直方图
            let mut hist = [0u32; 256];
            let tile_pixels = (x1 - x0 + 1) * (y1 - y0 + 1);
            for y in y0..=y1 {
                for x in x0..=x1 {
                    hist[img.get_pixel(x, y).0[0] as usize] += 1;
                }
            }

            // Clip 和分配
            let clip_limit_val = (clip_limit as f64 * tile_pixels as f64 / 256.0) as u32;
            let mut clipped = 0u32;
            for v in hist.iter_mut() {
                if *v > clip_limit_val {
                    clipped += *v - clip_limit_val;
                    *v = clip_limit_val;
                }
            }
            let redist = clipped / 256;
            for v in hist.iter_mut() {
                *v += redist;
            }

            // CDF
            let mut cdf = [0f64; 256];
            cdf[0] = hist[0] as f64;
            for i in 1..256 {
                cdf[i] = cdf[i-1] + hist[i] as f64;
            }
            let cdf_min = cdf.iter().cloned().find(|&v| v > 0.0).unwrap_or(0.0);
            for i in 0..256 {
                cdf[i] = (cdf[i] - cdf_min) / (tile_pixels as f64 - cdf_min) * 255.0;
            }

            // 映射
            for y in y0..=y1 {
                for x in x0..=x1 {
                    let p = img.get_pixel(x, y).0[0];
                    out.put_pixel(x, y, Luma([cdf[p as usize] as u8]));
                }
            }
        }
    }

    // 双线性插值去块效应
    bilinear_interpolation(&out, tile_size, tiles_x, tiles_y, img)
}

fn bilinear_interpolation(mapped: &GrayImage, tile_size: u32, tiles_x: u32, tiles_y: u32, original: &GrayImage) -> GrayImage {
    // 简化：不做完整双线性插值，直接返回 mapped
    mapped.clone()
}

/// 反转图像
fn invert_image(img: &GrayImage) -> GrayImage {
    let (w, h) = img.dimensions();
    GrayImage::from_fn(w, h, |x, y| {
        let p = img.get_pixel(x, y).0[0];
        Luma([255 - p])
    })
}

fn process_image(path: &PathBuf, args: &Args) -> Result<()> {
    let img = image::open(path)
        .with_context(|| format!("无法打开图片: {}", path.display()))?;

    // 转为灰度
    let gray = img.to_luma8();
    let mut img = gray;

    if args.verbose {
        println!("处理: {} ({}x{})", path.display(), img.width(), img.height());
    }

    // 预处理：CLAHE
    if let Some(tile) = args.clahe {
        img = clahe(&img, tile, 40);
        if args.verbose { println!("  → CLAHE 增强 (tile={})", tile); }
    }

    // 预处理：直方图均衡化
    if args.equalize {
        img = histogram_equalize(&img);
        if args.verbose { println!("  → 直方图均衡化"); }
    }

    // 预处理：高斯模糊
    if args.blur > 0.0 {
        img = gaussian_blur(&img, args.blur);
        if args.verbose { println!("  → 高斯模糊 (σ={})", args.blur); }
    }

    // 二值化
    let result: GrayImage = match args.method.as_str() {
        "global" => {
            let th = args.threshold.unwrap_or(128);
            if args.verbose { println!("  → 全局阈值: {}", th); }
            global_threshold(&img, th)
        }
        "adaptive" => {
            if args.verbose { println!("  → 自适应阈值 (window={}, C={})", args.window, args.c); }
            adaptive_threshold(&img, args.window, args.c)
        }
        "otsu" => {
            let hist = Histogram::from_gray(&img);
            let th = hist.otsu_threshold();
            if args.verbose { println!("  → Otsu 阈值: {}", th); }
            global_threshold(&img, th)
        }
        "triangle" => {
            let hist = Histogram::from_gray(&img);
            let th = hist.triangle_threshold();
            if args.verbose { println!("  → Triangle 阈值: {}", th); }
            global_threshold(&img, th)
        }
        "intermodes" => {
            let hist = Histogram::from_gray(&img);
            let th = hist.intermodes_threshold();
            if args.verbose { println!("  → Intermodes 阈值: {}", th); }
            global_threshold(&img, th)
        }
        "entropy" => {
            let hist = Histogram::from_gray(&img);
            let th = hist.entropy_threshold();
            if args.verbose { println!("  → Kapur 熵阈值: {}", th); }
            global_threshold(&img, th)
        }
        "minerror" => {
            let hist = Histogram::from_gray(&img);
            let th = hist.min_error_threshold();
            if args.verbose { println!("  → Minimum Error 阈值: {}", th); }
            global_threshold(&img, th)
        }
        _ => {
            eprintln!("未知方法: {}，使用 Otsu", args.method);
            let hist = Histogram::from_gray(&img);
            global_threshold(&img, hist.otsu_threshold())
        }
    };

    // 反转
    let result = if args.invert { invert_image(&result) } else { result };

    // 构建输出路径
    let out_dir = args.output_dir.clone().unwrap_or_else(|| {
        path.parent().unwrap_or(&PathBuf::from(".")).to_path_buf()
    });
    fs::create_dir_all(&out_dir)?;

    let stem = path.file_stem().unwrap().to_string_lossy();
    let ext = if args.format == "jpg" { "jpg" } else if args.format == "bmp" { "bmp" } else if args.format == "webp" { "webp" } else { "png" };
    let out_path = out_dir.join(format!("{}{}.{}", stem, args.suffix, ext));

    // 保存
    match ext {
        "png" => {
            result.save_with_format(&out_path, image::ImageFormat::Png)
                .context("保存 PNG 失败")?;
        }
        "jpg" => {
            result.save_with_format(&out_path, image::ImageFormat::Jpeg)
                .context("保存 JPEG 失败")?;
        }
        "bmp" => {
            result.save_with_format(&out_path, image::ImageFormat::Bmp)
                .context("保存 BMP 失败")?;
        }
        "webp" => {
            result.save_with_format(&out_path, image::ImageFormat::WebP)
                .context("保存 WebP 失败")?;
        }
        _ => {
            result.save(&out_path).context("保存图片失败")?;
        }
    }

    if args.verbose {
        println!("  ✓ 输出: {}", out_path.display());
    }

    Ok(())
}

fn main() -> Result<()> {
    let mut args = Args::parse();

    // GUI 模式
    if args.gui {
        return eframe::run_native(
            "图片二值化工具",
            eframe::NativeOptions::default(),
            Box::new(|_cc| Ok(Box::new(BinarizerApp::new(args)))),
        )
        .map_err(|e| anyhow::anyhow!("GUI 错误: {}", e));
    }

    // 加载配置文件
    if let Some(config_path) = &args.config {
        let content = fs::read_to_string(config_path)
            .with_context(|| format!("读取配置文件失败: {}", config_path.display()))?;
        let config: Config = serde_json::from_str(&content)?;
        if args.input.is_empty() && config.input.is_some() {
            args.input = config.input.unwrap();
        }
        if args.input_dir.is_none() && config.input_dir.is_some() {
            args.input_dir = config.input_dir;
        }
        if args.output_dir.is_none() && config.output_dir.is_some() {
            args.output_dir = config.output_dir;
        }
        // ... 同样合并其他字段
    }

    // 收集输入文件
    let mut files: Vec<PathBuf> = Vec::new();
    for pattern in &args.input {
        match glob::glob(pattern) {
            Ok(entries) => {
                for entry in entries.flatten() {
                    if entry.is_file() {
                        files.push(entry);
                    }
                }
            }
            Err(e) => eprintln!("通配符无效 '{}': {}", pattern, e),
        }
    }
    if let Some(dir) = &args.input_dir {
        if dir.is_dir() {
            for entry in fs::read_dir(dir)? {
                let entry = entry?;
                let path = entry.path();
                if path.is_file() {
                    if let Some(ext) = path.extension() {
                        let ext = ext.to_string_lossy().to_lowercase();
                        if matches!(ext.as_str(), "png" | "jpg" | "jpeg" | "bmp" | "webp" | "tiff" | "tif") {
                            files.push(path);
                        }
                    }
                }
            }
        }
    }

    if files.is_empty() {
        anyhow::bail!("没有找到可处理的图片文件。请使用 --input 指定文件或 --input-dir 指定目录。");
    }

    // 限制 PNG 压缩级别
    let png_compression = args.png_compression.min(9);

    for file in &files {
        process_image(file, &args)?;
    }

    println!("完成！共处理 {} 个文件。", files.len());
    Ok(())
}

use eframe::egui;

struct BinarizerApp {
    args: Args,
    // GUI state
}

impl BinarizerApp {
    fn new(args: Args) -> Self {
        Self { args }
    }
}

impl eframe::App for BinarizerApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("图片二值化工具");
            ui.separator();
            ui.label("请使用命令行模式运行完整功能。");
        });
    }
}
