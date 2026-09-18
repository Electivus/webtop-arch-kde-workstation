async page => {
    if (!/^https:\/\/(?:localhost|127\.0\.0\.1):14512(?:\/|$)/.test(page.url())) {
        throw new Error('Use only the dedicated Latitude verification desktop.');
    }
    await page.setViewportSize({ width: 1920, height: 1080 });
    const canvas = page.locator('canvas').first();
    await canvas.waitFor({ state: 'visible' });
    const box = await canvas.boundingBox();
    await page.screenshot({ path: '.local/latitude-desktop.png' });
    const clip = { x: box.x + box.width * 1400 / 1920, y: box.y + box.height * 550 / 1080,
        width: 24, height: 24 };
    async function pixel() {
        const png = await page.screenshot({ clip });
        return page.evaluate(async bytes => {
            const bitmap = await createImageBitmap(new Blob([new Uint8Array(bytes)], { type: 'image/png' }));
            const offscreen = document.createElement('canvas');
            offscreen.width = bitmap.width;
            offscreen.height = bitmap.height;
            const context = offscreen.getContext('2d');
            context.drawImage(bitmap, 0, 0);
            const rgba = [...context.getImageData(12, 12, 1, 1).data];
            bitmap.close();
            return rgba;
        }, [...png]);
    }
    const isColor = (rgba, red) => red ? rgba[0] > 150 && rgba[2] < 80 : rgba[2] > 150 && rgba[0] < 80;
    const initial = await pixel();
    if (!isColor(initial, false)) throw new Error('Expected the visible blue Chrome probe at the sampling point: ' + initial);
    // Editor startup can claim focus after its window first appears. Activate
    // the measured Chrome page through the same streamed pointer as the user.
    await page.mouse.click(clip.x + 12, clip.y + 12);
    const samples = [];
    for (let index = 0; index < 10; index++) {
        const red = index % 2 === 0;
        const started = await page.evaluate(() => performance.now());
        await page.keyboard.press('t');
        let rgba, elapsed;
        do {
            rgba = await pixel();
            elapsed = await page.evaluate(start => performance.now() - start, started);
            if (isColor(rgba, red)) break;
        } while (elapsed < 3000);
        if (!isColor(rgba, red)) throw new Error('No observed response to streamed keyboard input: ' + rgba);
        samples.push({ milliseconds: Math.round(elapsed * 10) / 10, rgba });
    }
    await page.screenshot({ path: '.local/latitude-desktop.png' });
    return { desktop: { width: 1920, height: 1080 }, canvas: box, sampleClip: clip, samples,
        method: 'Keyboard input through Webtop until the expected decoded Chrome color is observed in a screenshot; includes automation and capture overhead.' };
}
