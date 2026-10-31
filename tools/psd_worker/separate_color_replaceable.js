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
    input = input ? path.resolve(input) : path.join(ciktiDir, 'hedef_desen.jpg');
    outPsd = outPsd ? path.resolve(outPsd) : path.join(ciktiDir, 'zirh_desen_renk_ayrimli.psd');
    outDir = outDir ? path.resolve(outDir) : ciktiDir;
    return { input, outPsd, outDir };
}

async function createColorReplaceablePSD() {
    const { input: inputPath, outPsd: outPsdPath, outDir: outPngDir } = parseArgs();
    fs.mkdirSync(outPngDir, { recursive: true });
    fs.mkdirSync(path.dirname(outPsdPath), { recursive: true });

    console.log("Loading target image:", inputPath);
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

    // We will create structured semantic layers designed for easy color replacement:
    // Katman 1: Zemin (Saf Siyah Kumaş Tabanı)
    // Katman 2: Konturlar ve Gölgeler (Siyah/Koyu Çizgiler - Alttaki renklerin üzerinde kalacak 'Multiply' katmanı)
    // Katman 3: Koyu Antrasit Zırh Plakaları (Zırhın metal gövdesi)
    // Katman 4: Kızıl & Yanık Bakır Dokular (Omuz, yaka ve pas/alev desenleri - Ayrı Hue/Saturation için)
    // Katman 5: Bronz & Altın Metalik Vurgular (Göğüs kafatası, alt amblem, kemer kafatasları, boynuzlar, tokalar)
    // Katman 6: Kırmızı Akkor Gözler ve Kor Parıltısı (Gözlerin kırmızı ışıltısı)

    const bgCanvas = createCanvas(width, height);
    const bgCtx = bgCanvas.getContext('2d');
    const bgData = bgCtx.createImageData(width, height);

    const darkLinesCanvas = createCanvas(width, height);
    const darkLinesCtx = darkLinesCanvas.getContext('2d');
    const darkLinesData = darkLinesCtx.createImageData(width, height);

    const metalBaseCanvas = createCanvas(width, height);
    const metalBaseCtx = metalBaseCanvas.getContext('2d');
    const metalBaseData = metalBaseCtx.createImageData(width, height);

    const redEmberCanvas = createCanvas(width, height);
    const redEmberCtx = redEmberCanvas.getContext('2d');
    const redEmberData = redEmberCtx.createImageData(width, height);

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

        // Background is always solid black
        bgData.data[idx] = 0;
        bgData.data[idx + 1] = 0;
        bgData.data[idx + 2] = 0;
        bgData.data[idx + 3] = 255;

        const maxVal = Math.max(r, g, b);
        const lum = 0.299 * r + 0.587 * g + 0.114 * b;

        // Skip pure background
        if (maxVal < 14) {
            continue;
        }

        // 1. Akkor Gözler (Parlak kırmızı / turuncu-kırmızı gözler)
        if (r > 130 && r > (g * 1.7) && r > (b * 1.7)) {
            eyeData.data[idx] = r;
            eyeData.data[idx + 1] = g;
            eyeData.data[idx + 2] = b;
            eyeData.data[idx + 3] = 255;
            continue;
        }

        // 2. Kırmızı / Yanık Bakır & Pas / Kumaş Dokuları
        // Distinct red-brown / rust tone
        const isRustOrEmber = (r > 50 && r > (g * 1.35) && r > (b * 1.3) && g < 80);
        if (isRustOrEmber) {
            redEmberData.data[idx] = r;
            redEmberData.data[idx + 1] = g;
            redEmberData.data[idx + 2] = b;
            redEmberData.data[idx + 3] = 255;
            continue;
        }

        // 3. Bronz & Altın Metalik İşlemeler (Kafatasları, boynuzlar, çerçeveler)
        // Warm gold/bronze metallic where R > B and G > B and brightness is moderate to high
        const isBronzeWarm = (r > 65 && g > 45 && r >= g && g > b * 1.15 && lum >= 45);
        if (isBronzeWarm) {
            bronzeData.data[idx] = r;
            bronzeData.data[idx + 1] = g;
            bronzeData.data[idx + 2] = b;
            bronzeData.data[idx + 3] = 255;
            continue;
        }

        // 4. Koyu Gölgeler ve Kontur Çizgileri (Line art & deep shadows)
        if (lum < 35) {
            darkLinesData.data[idx] = r;
            darkLinesData.data[idx + 1] = g;
            darkLinesData.data[idx + 2] = b;
            // Opacity based on darkness
            darkLinesData.data[idx + 3] = Math.min(255, Math.round((35 - lum) * 7.5 + 50));
            // Also give faint base in metal
            metalBaseData.data[idx] = r;
            metalBaseData.data[idx + 1] = g;
            metalBaseData.data[idx + 2] = b;
            metalBaseData.data[idx + 3] = 120;
            continue;
        }

        // 5. Koyu Zırh Gövdesi ve Plakalar
        metalBaseData.data[idx] = r;
        metalBaseData.data[idx + 1] = g;
        metalBaseData.data[idx + 2] = b;
        metalBaseData.data[idx + 3] = 255;
    }

    bgCtx.putImageData(bgData, 0, 0);
    darkLinesCtx.putImageData(darkLinesData, 0, 0);
    metalBaseCtx.putImageData(metalBaseData, 0, 0);
    redEmberCtx.putImageData(redEmberData, 0, 0);
    bronzeCtx.putImageData(bronzeData, 0, 0);
    eyeCtx.putImageData(eyeData, 0, 0);

    // Write PNG outputs
    fs.writeFileSync(path.join(outPngDir, "katman_1_zemin_siyah.png"), bgCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_2_koyu_zirh_plakalari.png"), metalBaseCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_3_kizil_ve_yanik_bakir_dokular.png"), redEmberCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_4_bronz_kafatasi_ve_islemeler.png"), bronzeCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_5_koyu_cizgiler_ve_konturlar.png"), darkLinesCanvas.toBuffer('image/png'));
    fs.writeFileSync(path.join(outPngDir, "katman_6_kirmizi_akkor_gozler.png"), eyeCanvas.toBuffer('image/png'));
    console.log("Color replaceable PNG layers saved.");

    // Structured PSD for easy color replacement (Hue/Saturation, Color Overlay)
    const psdStructure = {
        width: width,
        height: height,
        canvas: baseCanvas,
        children: [
            {
                name: "1 - Zemin (Kumas Rengi)",
                canvas: bgCanvas,
                blendMode: "normal",
                opacity: 1
            },
            {
                name: "2 - Koyu Demir Zirh Plakalari",
                canvas: metalBaseCanvas,
                blendMode: "normal",
                opacity: 1
            },
            {
                name: "3 - Kizil ve Yanik Bakir Dokular (Renk Degisimi)",
                canvas: redEmberCanvas,
                blendMode: "normal",
                opacity: 1
            },
            {
                name: "4 - Bronz Kafataslari ve Boynuzlar (Metal Renk Degisimi)",
                canvas: bronzeCanvas,
                blendMode: "normal",
                opacity: 1
            },
            {
                name: "5 - Konturlar ve Golgeler",
                canvas: darkLinesCanvas,
                blendMode: "multiply",
                opacity: 0.9
            },
            {
                name: "6 - Kirmizi Akkor Gozler (Isilti Degisimi)",
                canvas: eyeCanvas,
                blendMode: "screen",
                opacity: 1
            }
        ]
    };

    const buffer = Buffer.from(writePsd(psdStructure));
    fs.writeFileSync(outPsdPath, buffer);
    console.log("Color replaceable layered PSD created at:", outPsdPath);
    console.log("File size (bytes):", buffer.length);
}

createColorReplaceablePSD().catch(err => {
    console.error("Error creating PSD:", err);
    process.exit(1);
});
