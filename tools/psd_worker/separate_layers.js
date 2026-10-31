const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('canvas');
const { writePsd } = require('ag-psd');

function parseArgs() {
    const args = process.argv.slice(2);
    let input = null, outPsd = null, outDir = null;
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--input' && args[i + 1]) input = args[++i];
        else if (args[i] === '--out-psd' && args[i + 1]) outPsd = args[++i];
        else if (args[i] === '--output' && args[i + 1]) outDir = args[++i];
        else if (!args[i].startsWith('--')) {
            if (!input) input = args[i];
            else if (!outPsd) outPsd = args[i];
            else if (!outDir) outDir = args[i];
        }
    }
    const ciktiDir = path.resolve(__dirname, '../../cikti');
    input = input ? path.resolve(input) : path.join(ciktiDir, 'armor_2d_flat.jpg');
    outPsd = outPsd ? path.resolve(outPsd) : path.join(ciktiDir, 'desen_katmanli.psd');
    outDir = outDir ? path.resolve(outDir) : ciktiDir;
    return { input, outPsd, outDir };
}

async function processImageToPSD() {
    const { input: inputPath, outPsd: outPsdPath, outDir: outPngDir } = parseArgs();
    fs.mkdirSync(outPngDir, { recursive: true });
    fs.mkdirSync(path.dirname(outPsdPath), { recursive: true });

    console.log("Loading image:", inputPath);
    const img = await loadImage(inputPath);
    const width = img.width;
    const height = img.height;
    console.log(`Image dimensions: ${width}x${height}`);

    // Base canvas to extract raw pixels
    const baseCanvas = createCanvas(width, height);
    const baseCtx = baseCanvas.getContext('2d');
    baseCtx.drawImage(img, 0, 0);
    const srcData = baseCtx.getImageData(0, 0, width, height);
    const pixels = srcData.data;
    const totalPixels = width * height;

    // We will separate into 4 functional semantic layers:
    // 1. Zemin (Siyah / Kumaş arka plan)
    // 2. Koyu Metal & Zırh Gövdesi (Karanlık zırh plakaları ve taban)
    // 3. Bronz & Bakır Detaylar (Kafatasının hatları, boynuzlar, oymalar)
    // 4. Kırmızı Parıltı & Vurgular (Gözler, ateş/kor ışıltıları)

    const bgCanvas = createCanvas(width, height);
    const bgCtx = bgCanvas.getContext('2d');
    const bgImgData = bgCtx.createImageData(width, height);

    const metalCanvas = createCanvas(width, height);
    const metalCtx = metalCanvas.getContext('2d');
    const metalImgData = metalCtx.createImageData(width, height);

    const bronzeCanvas = createCanvas(width, height);
    const bronzeCtx = bronzeCanvas.getContext('2d');
    const bronzeImgData = bronzeCtx.createImageData(width, height);

    const redCanvas = createCanvas(width, height);
    const redCtx = redCanvas.getContext('2d');
    const redImgData = redCtx.createImageData(width, height);

    for (let i = 0; i < totalPixels; i++) {
        const idx = i * 4;
        const r = pixels[idx];
        const g = pixels[idx + 1];
        const b = pixels[idx + 2];
        const a = pixels[idx + 3];

        // Luminance / Brightness
        const lum = 0.299 * r + 0.587 * g + 0.114 * b;

        // Check for Black Background threshold (pure darkness)
        // Soft alpha calculation from background
        if (lum < 15 && Math.max(r, g, b) < 25) {
            // Pure background
            bgImgData.data[idx] = 0;
            bgImgData.data[idx + 1] = 0;
            bgImgData.data[idx + 2] = 0;
            bgImgData.data[idx + 3] = 255;
            continue;
        }

        // Always put black in background layer for clean base
        bgImgData.data[idx] = 0;
        bgImgData.data[idx + 1] = 0;
        bgImgData.data[idx + 2] = 0;
        bgImgData.data[idx + 3] = 255;

        // Check for Red Glow (Glowing eyes and crimson embers)
        // High red relative to green/blue or strong reddish saturation
        const isRedGlow = (r > 120 && r > (g * 1.6) && r > (b * 1.6)) || (r > 180 && g < 80 && b < 80);

        if (isRedGlow) {
            redImgData.data[idx] = r;
            redImgData.data[idx + 1] = g;
            redImgData.data[idx + 2] = b;
            redImgData.data[idx + 3] = 255;
            // Also contribute softer tone to underlying bronze/metal for natural blending
            metalImgData.data[idx] = Math.round(r * 0.3);
            metalImgData.data[idx + 1] = Math.round(g * 0.3);
            metalImgData.data[idx + 2] = Math.round(b * 0.3);
            metalImgData.data[idx + 3] = 255;
            continue;
        }

        // Check for Bronze/Gold Highlights vs Dark Metal Plate
        // Warm tones with medium to high brightness
        const isBronze = (r > 70 && g > 40 && lum >= 50);

        if (isBronze) {
            bronzeImgData.data[idx] = r;
            bronzeImgData.data[idx + 1] = g;
            bronzeImgData.data[idx + 2] = b;
            bronzeImgData.data[idx + 3] = 255;
        } else {
            // Dark Metal Armor base
            metalImgData.data[idx] = r;
            metalImgData.data[idx + 1] = g;
            metalImgData.data[idx + 2] = b;
            // Smooth alpha falloff near background
            const alphaVal = Math.min(255, Math.max(0, Math.round((lum - 10) * 10)));
            metalImgData.data[idx + 3] = alphaVal;
        }
    }

    bgCtx.putImageData(bgImgData, 0, 0);
    metalCtx.putImageData(metalImgData, 0, 0);
    bronzeCtx.putImageData(bronzeImgData, 0, 0);
    redCtx.putImageData(redImgData, 0, 0);

    // Save individual PNG layers for direct screen print / inspection
    fs.writeFileSync(path.join(outPngDir, "katman_1_zemin.png"), bgCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_2_koyu_metal.png"), metalCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_3_bronz_isiltilar.png"), bronzeCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_4_kirmizi_gozler.png"), redCanvas.toBuffer('image/png'));
    console.log("PNG layers saved successfully.");

    // Create layered PSD using ag-psd
    const psdStructure = {
        width: width,
        height: height,
        canvas: baseCanvas,
        children: [
            {
                name: "1 - Zemin (Siyah)",
                canvas: bgCanvas,
                blendMode: "normal",
                opacity: 1
            },
            {
                name: "2 - Koyu Zırh Plakaları",
                canvas: metalCanvas,
                blendMode: "normal",
                opacity: 1
            },
            {
                name: "3 - Bronz ve Bakır İşlemeler",
                canvas: bronzeCanvas,
                blendMode: "normal",
                opacity: 1
            },
            {
                name: "4 - Kırmızı Gözler ve Parıltı",
                canvas: redCanvas,
                blendMode: "screen",
                opacity: 1
            }
        ]
    };

    const buffer = Buffer.from(writePsd(psdStructure));
    fs.writeFileSync(outPsdPath, buffer);
    console.log("Layered PSD file created at:", outPsdPath);
    console.log("File size (bytes):", buffer.length);
}

processImageToPSD().catch(err => {
    console.error("Error creating PSD:", err);
    process.exit(1);
});
