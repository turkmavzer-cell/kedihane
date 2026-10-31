// [ÖRNEK BETİK]
const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('canvas');
const { writePsd } = require('ag-psd');

function parseArgs() {
    const args = process.argv.slice(2);
    let input = null, outPsd = null, output = null;
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--input' && args[i + 1]) input = args[++i];
        else if (args[i] === '--out-psd' && args[i + 1]) outPsd = args[++i];
        else if (args[i] === '--output' && args[i + 1]) output = args[++i];
        else if (!args[i].startsWith('--')) {
            if (!input) input = args[i];
            else if (!outPsd) outPsd = args[i];
            else if (!output) output = args[i];
        }
    }
    const ciktiDir = path.resolve(__dirname, '../../cikti');
    input = input ? path.resolve(input) : path.join(ciktiDir, 'layers');
    outPsd = outPsd ? path.resolve(outPsd) : path.join(__dirname, '..', '..', 'cikti', 'deneme_1.psd');
    output = output ? path.resolve(output) : null;
    return { input, outPsd, output };
}

async function createDeneme1PSD() {
    const { input: layersDir, outPsd: outPsdLocal, output: outPsdDownloads } = parseArgs();
    fs.mkdirSync(path.dirname(outPsdLocal), { recursive: true });

    console.log("Loading layer images from:", layersDir);

    const layerDefs = [
        { file: 'orijinal_referans.png', name: '0 - Orijinal Referans (Ham Görsel)', blendMode: 'normal', opacity: 1, hidden: true },
        { file: 'zemin_siyah.png', name: '0b - Zemin (Alternatif Siyah)', blendMode: 'normal', opacity: 1, hidden: true },
        { file: 'zemin_beyaz.png', name: '1 - Zemin (Beyaz Taban)', blendMode: 'normal', opacity: 1, hidden: false },
        { file: 'katman_2_koyu_metal_govde.png', name: '2 - Koyu Metal & Döküm Zırh Gövdesi', blendMode: 'normal', opacity: 1, hidden: false },
        { file: 'katman_3_acik_metal_ve_gumus.png', name: '3 - Açık Metal & Gümüş Vurgular', blendMode: 'normal', opacity: 1, hidden: false },
        { file: 'katman_4_bronz_ve_bakir.png', name: '4 - Bronz & Yanık Bakır Dokular', blendMode: 'normal', opacity: 1, hidden: false },
        { file: 'katman_5_sari_altin_ve_pirinc.png', name: '5 - Sarı Altın & Pirinç İşlemeler', blendMode: 'normal', opacity: 1, hidden: false },
        { file: 'katman_6_koyu_konturlar_ve_golgeler.png', name: '6 - Koyu Çizgiler & Konturlar', blendMode: 'multiply', opacity: 1, hidden: false },
        { file: 'katman_7_kirmizi_akkor_gozler.png', name: '7 - Kırmızı Akkor Gözler & Parıltılar', blendMode: 'screen', opacity: 1, hidden: false },
        { file: 'katman_yan_parcalar_ve_zincir.png', name: '8 - Yan Detaylar & Zincir Parçaları', blendMode: 'normal', opacity: 1, hidden: false }
    ];

    const children = [];
    let width = 1024;
    let height = 1536;
    let baseCanvas = null;

    for (const def of layerDefs) {
        const filePath = path.join(layersDir, def.file);
        if (!fs.existsSync(filePath)) {
            console.error(`Missing layer file: ${filePath}`);
            continue;
        }

        const img = await loadImage(filePath);
        width = img.width;
        height = img.height;

        const canvas = createCanvas(width, height);
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);

        if (!baseCanvas) {
            baseCanvas = canvas;
        }

        children.push({
            name: def.name,
            canvas: canvas,
            blendMode: def.blendMode,
            opacity: def.opacity,
            hidden: def.hidden
        });
        console.log(`Loaded layer: ${def.name}`);
    }

    if (!baseCanvas) {
        console.warn("No layer images could be loaded from:", layersDir);
        return;
    }

    const psdStructure = {
        width: width,
        height: height,
        canvas: baseCanvas,
        children: children
    };

    console.log("Writing PSD binary...");
    const buffer = Buffer.from(writePsd(psdStructure));

    // Save local copy
    fs.writeFileSync(outPsdLocal, buffer);
    console.log(`Saved local copy: ${outPsdLocal}`);

    // Save to secondary output if directory exists
    if (outPsdDownloads && fs.existsSync(path.dirname(outPsdDownloads))) {
        try {
            fs.writeFileSync(outPsdDownloads, buffer);
            console.log(`Saved to output: ${outPsdDownloads} (${buffer.length} bytes)`);
        } catch (e) {
            console.warn(`Could not write to output: ${e.message}`);
        }
    }

    console.log("PSD generation completed successfully!");
}

createDeneme1PSD().catch(err => {
    console.error("Error creating PSD:", err);
    process.exit(1);
});
