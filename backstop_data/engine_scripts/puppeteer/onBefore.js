module.exports = async (page, scenario) => {
  await page.goto(scenario.url, { waitUntil: 'networkidle2' });

  console.log('Page loaded.');

  // Count the number of items in the side navigation and log their text
  const navItems = await page.$$eval('nav ul li.usa-sidenav__item a', (items) =>
    items.map((item) => item.textContent.trim())
  );

  console.log(`Found ${navItems.length} navigation items:`);
  navItems.forEach((itemText, index) => {
    console.log(`${index + 1}: ${itemText}`);
  });

  // Wait a moment for the logging to complete
  await new Promise((resolve) => setTimeout(resolve, 1000));
};
