// 通过Chrome DevTools Protocol 直接设置 file input
// 使用 Chrome 的 setFileInputFiles 方法

const http = require('http');
const { spawn } = require('child_process');

const FILE_PATH = 'E:\\openclaw压缩包及启动教程\\u-claw\\portable\\data\\.openclaw\\workspace\\source.jpg';

// 先通过浏览器自动化的CDP接口来设置文件上传
// Playwright/CDP 的 setInputFiles 是标准做法

async function main() {
  // 尝试通过暴露的CDP接口 - 查找Chrome调试端口
  // Chrome启动时如果没有指定调试端口，默认是没有的
  // 我们需要通过另一种方式
  
  const puppeteer = require('puppeteer-core');
  
  // 连接正在运行的Chrome实例
  // 首先查找它的调试端口
  const { execSync } = require('child_process');
  try {
    const result = execSync('netstat -ano | findstr "9222"').toString();
    console.log('Found ports:', result);
  } catch (e) {
    console.log('No 9222 port found, will try other ports');
  }
  
  // 尝试连接
  try {
    const browser = await puppeteer.connect({
      browserURL: 'http://127.0.0.1:9222',
      defaultViewport: null
    });
    console.log('Connected to Chrome');
    
    const pages = await browser.pages();
    console.log('Pages:', pages.length);
    
    // 找到豆包页面
    for (const page of pages) {
      if (page.url().includes('doubao.com') || page.url().includes('dreamina')) {
        console.log('Found target page:', page.url());
        
        // 找到file input
        const input = await page.$('input[type="file"]');
        if (input) {
          console.log('Found file input, setting file...');
          await input.setInputFiles(FILE_PATH);
          console.log('File set successfully!');
        } else {
          console.log('File input not found');
        }
        break;
      }
    }
    
    await browser.disconnect();
  } catch (e) {
    console.error('Failed to connect:', e.message);
  }
}

main().catch(console.error);
