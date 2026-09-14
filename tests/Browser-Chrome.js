async page => {
    await page.keyboard.type("google-chrome --new-window 'data:text/html,<title>Workstation browser</title><h1>Chrome is ready</h1><p>Official Google Chrome on Arch KDE</p>' > /config/chrome-desktop.log 2>&1 &", { delay: 12 });
    await page.keyboard.press('Enter');
    return { url: page.url(), title: await page.title(), launchedFromDesktopTerminal: true };
}
