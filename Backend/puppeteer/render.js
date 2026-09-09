const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    defaultViewport: {
      width: 1280,
      height: 720,
    },
  });

  const page = await browser.newPage();
  const html = 'file://' + path.resolve('generated/slides.html');
  await page.goto(html, { waitUntil: 'networkidle2' });
  await page.waitForSelector('body');
  await sleep(1000);

  const framesDir = path.resolve('generated/frames');
  if (!fs.existsSync(framesDir)) {
    fs.mkdirSync(framesDir, { recursive: true });
  }

  const slideCount = parseInt(process.argv[2], 10);
  for (let i = 0; i < slideCount; i++) {
    await page.screenshot({
      path: path.join(framesDir, `slide${i + 1}.png`),
    });

    if (i < slideCount - 1) {
      await page.keyboard.press('ArrowRight');
      await sleep(500);
    }
  }

  await browser.close();
})();