const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('canvas');

function parseArgs() {
    const args = process.argv.slice(2);
    let input = null, output = null, size = 800;
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--input' && args[i + 1]) input = args[++i];
        else if (args[i] === '--output' && args[i + 1]) output = args[++i];
        else if (args[i] === '--size' && args[i + 1]) size = parseInt(args[++i], 10) || 800;
        else if (!args[i].startsWith('--')) {
            if (!input) input = args[i];
            else if (!output) output = args[i];
            else if (!size) size = parseInt(args[i], 10) || 800;
        }
    }
    const defaultSrc = process.env.THUMBS_SRC_DIR || path.join(__dirname, '..', '..', 'cikti', 'girdi_gorseller');
    const defaultOut = process.env.THUMBS_OUT_DIR || path.join(__dirname, '..', '..', 'cikti', 'onizleme_thumbs');
    return {
        srcDir: input ? path.resolve(input) : defaultSrc,
        destDir: output ? path.resolve(output) : defaultOut,
        maxSize: size || 800
    };
}

async function createThumbnails() {
    const { srcDir, destDir, maxSize } = parseArgs();
    fs.mkdirSync(destDir, { recursive: true });

    let files = ['model 1.jpg', 'model 2.jpg', 'model 3.jpg', 'model 4.jpg'];
    if (fs.existsSync(srcDir)) {
        const dirFiles = fs.readdirSync(srcDir).filter(f => /\.(jpe?g|png)$/i.test(f));
        if (dirFiles.length > 0) files = dirFiles;
    }

    for (const f of files) {
        const fullPath = path.join(srcDir, f);
        if (!fs.existsSync(fullPath)) {
            console.warn('File not found, skipping:', fullPath);
            continue;
        }
        console.log('Loading:', fullPath);
        const img = await loadImage(fullPath);
        console.log(f, 'dimensions:', img.width, 'x', img.height);
        
        // Scale down to max size for fast preview and inspection
        const scale = Math.min(maxSize / img.width, maxSize / img.height, 1);
        const w = Math.round(img.width * scale);
        const h = Math.round(img.height * scale);
        
        const canvas = createCanvas(w, h);
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, w, h);
        
        const outPath = path.join(destDir, f.replace(/\.(jfif|jpg|jpeg|png)$/i, '.jpg'));
        fs.writeFileSync(outPath, canvas.toBuffer('image/jpeg'));
        console.log('Thumbnail saved:', outPath);
    }
}
createThumbnails().catch(console.error);
