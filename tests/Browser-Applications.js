async page => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.locator('canvas').first().waitFor({ state: 'visible' });
    // The harness opens and activates a real Konsole window using X11;
    // the completed preparation window can otherwise retain keyboard focus.
    await page.waitForTimeout(500);
    await page.keyboard.type("git --version; google-chrome --version; zsh --version; touch /config/t02-terminal-ready", { delay: 20 });
    await page.keyboard.press('Enter');
    return { url: page.url(), terminalCommandsSubmitted: true };
}
