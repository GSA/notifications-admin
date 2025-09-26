module.exports = async (page, scenario, vp) => {
  console.log('SCENARIO > ' + scenario.label);

  await page.evaluate(async () => {
    const selectors = Array.from(document.images);
    await Promise.all(selectors.map(img => {
      if (img.complete) return;
      return new Promise((resolve, reject) => {
        img.addEventListener('load', resolve);
        img.addEventListener('error', resolve);
        setTimeout(resolve, 5000);
      });
    }));
  });

  await page.waitForSelector('.usa-banner__header-flag', {
    visible: true,
    timeout: 10000
  });

  await page.evaluate(() => {
    const flagImg = document.querySelector('.usa-banner__header-flag');
    if (flagImg && !flagImg.complete) {
      return new Promise((resolve) => {
        flagImg.onload = resolve;
        flagImg.onerror = resolve;
        setTimeout(resolve, 3000);
      });
    }
  });

  await new Promise(resolve => setTimeout(resolve, 500));

  console.log('All images loaded and layout stable for: ' + scenario.label);
};
