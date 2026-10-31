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
    input = input ? path.resolve(input) : path.join(ciktiDir, 'gemini_desen_orijinal.jpg');
    outPsd = outPsd ? path.resolve(outPsd) : path.join(ciktiDir, 'desen_katmanli_tam.psd');
    outDir = outDir ? path.resolve(outDir) : ciktiDir;
    return { input, outPsd, outDir };
}

async function separateGeminiResult() {
    const { input: inputPath, outPsd: outPsdPath, outDir: outPngDir } = parseArgs();
    fs.mkdirSync(outPngDir, { recursive: true });
    fs.mkdirSync(path.dirname(outPsdPath), { recursive: true });

    console.log("Loading user's Gemini generated image:", inputPath);
    const img = await loadImage(inputPath);
    const width = img.width;
    const height = img.height;
    console.log(`Dimensions: ${width}x${height}`);

    const baseCanvas = createCanvas(width, height);
    const baseCtx = baseCanvas.getContext('2d');
    baseCtx.drawImage(img, 0, 0);
    const srcData = baseCtx.getImageData(0, 0, width, height);
    const pixels = srcData.data;
    const totalPixels = width * height;

    // We will separate into 5 professional screen-printing / Photoshop design layers:
    // 1. Zemin (Siyah arka plan)
    // 2. Kırmızı Kumaş & Alt Yaka (Yaka ve kol altındaki kızıl dokular)
    // 3. Koyu Zırh Gövdesi & Plakalar (Antrasit / döküm demir zırh katmanı)
    // 4. Bronz & Pirinç İşlemeler (Kafatasları, boynuzlar, zincirler, oymalı kenarlıklar)
    // 5. Kırmızı Akkor Gözler (Parlayan kırmızı göz yuvaları)

    const bgCanvas = createCanvas(width, height);
    const bgCtx = bgCanvas.getContext('2d');
    const bgData = bgCtx.createImageData(width, height);

    const fabricCanvas = createCanvas(width, height);
    const fabricCtx = fabricCanvas.getContext('2d');
    const fabricData = fabricCtx.createImageData(width, height);

    const armorCanvas = createCanvas(width, height);
    const armorCtx = armorCanvas.getContext('2d');
    const armorData = armorCtx.createImageData(width, height);

    const bronzeCanvas = createCanvas(width, height);
    const bronzeCtx = bronzeCanvas.getContext('2d');
    const bronzeData = bronzeCtx.createImageData(width, height);

    const eyeCanvas = createCanvas(width, height);
    const eyeCtx = eyeCanvas.getContext('2d');
    const eyeData = eyeCtx.createImageData(width, height);

    for (let i = 0; i < totalPixels; i++) {
        const idx = i * 4;
        const r = pixels[idx];
        const g = pixels[idx + 1];
        const b = pixels[idx + 2];

        // Background always solid black base
        bgData.data[idx] = 0;
        bgData.data[idx + 1] = 0;
        bgData.data[idx + 2] = 0;
        bgData.data[idx + 3] = 255;

        const maxVal = Math.max(r, g, b);
        const lum = 0.299 * r + 0.587 * g + 0.114 * b;

        // Skip pure background
        if (maxVal < 18) {
            continue;
        }

        // Layer 5: Kırmızı Akkor Gözler
        // Strongly saturated red
        if (r > 140 && r > (g * 1.8) && r > (b * 1.8)) {
            eyeData.data[idx] = r;
            eyeData.data[idx + 1] = g;
            eyeData.data[idx + 2] = b;
            eyeData.data[idx + 3] = 255;
            continue;
        }

        // Layer 2: Kırmızı Kumaş & Yaka / Pas tonları
        // Muted crimson / wine red
        if (r > 60 && r > (g * 1.4) && r > (b * 1.3) && (g < 60)) {
            fabricData.data[idx] = r;
            fabricData.data[idx + 1] = g;
            fabricData.data[idx + 2] = b;
            fabricData.data[idx + 3] = 255;
            continue;
        }

        // Layer 4: Bronz & Pirinç İşlemeler (Kafatasları, oymalar, zincirler, boynuzlar)
        // Warm metallic colors: warm hue where r > b and g > b
        const isWarmMetallic = (r > 75 && g > 55 && (r >= g) && (g > b * 1.05));
        const isHighlight = lum > 110;

        if (isWarmMetallic || (isHighlight && (r >= b))) {
            bronzeData.data[idx] = r;
            bronzeData.data[idx + 1] = g;
            bronzeData.data[idx + 2] = b;
            bronzeData.data[idx + 3] = 255;
        } else {
            // Layer 3: Koyu Zırh Gövdesi
            armorData.data[idx] = r;
            armorData.data[idx + 1] = g;
            armorData.data[idx + 2] = b;
            // Smooth edge alpha
            const alphaVal = Math.min(255, Math.max(0, Math.round((maxVal - 15) * 8)));
            armorData.data[idx + 3] = alphaVal;
        }
    }

    bgCtx.putImageData(bgData, 0, 0);
    fabricCtx.putImageData(fabricData, 0, 0);
    armorCtx.putImageData(armorData, 0, 0);
    bronzeCtx.putImageData(bronzeData, 0, 0);
    eyeCtx.putImageData(eyeData, 0, 0);

    // Save PNG layers
    fs.writeFileSync(path.join(outPngDir, "katman_1_zemin.png"), bgCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_2_kirmizi_kumas_ve_yaka.png"), fabricCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_3_koyu_zirh_govdesi.png"), armorCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_4_bronz_kafatasi_ve_zincirler.png"), bronzeCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_5_kirmizi_akkor_gozler.png"), eyeCanvas.toBuffer('image/png'));
    console.log("Separated PNG layers written successfully.");

    // Create PSD
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
                name: "2 - Kırmızı Kumaş ve Yaka",
                canvas: fabricCanvas,
                blendMode: "normal",
                opacity: 1
            },
            {
                name: "3 - Koyu Döküm Zırh Gövdesi",
                canvas: armorCanvas,
                blendMode: "normal",
                opacity: 1
            },
            {
                name: "4 - Bronz Kafatası, Boynuzlar ve Zincirler",
                canvas: bronzeCanvas,
                blendMode: "normal",
                opacity: 1
            },
            {
                name: "5 - Kırmızı Akkor Gözler",
                canvas: eyeCanvas,
                blendMode: "screen",
                opacity: 1
            }
        ]
    };

    const buffer = Buffer.from(writePsd(psdStructure));
    fs.writeFileSync(outPsdPath, buffer);
    console.log("Final layered PSD created:", outPsdPath);
    console.log("PSD Size (bytes):", buffer.length);
}

separateGeminiResult().catch(err => {
    console.error("Error separating layers:", err);
    process.exit(1);
});
