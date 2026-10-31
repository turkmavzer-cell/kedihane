#target photoshop
// Betikle ayni klasordeki katmanlar.json + tam tuval PNG katmanlarindan PSD kurar (duplicate ile hiza korunur).
app.displayDialogs = DialogModes.NO;
app.preferences.rulerUnits = Units.PIXELS;
var root = new File($.fileName).parent;
var jf = new File(root.fsName + "/katmanlar.json"); jf.encoding = "UTF-8"; jf.open("r");
var meta = eval("(" + jf.read() + ")"); jf.close();
var doc = null;
for (var i = 0; i < meta.layers.length; i++) {
  var L = meta.layers[i];
  var src = app.open(new File(root.fsName + "/" + L.file));
  if (i == 0) { doc = src; doc.activeLayer.isBackgroundLayer = false; doc.activeLayer.name = L.name; continue; }
  var lyr = src.activeLayer;
  lyr.duplicate(doc, ElementPlacement.PLACEATBEGINNING);
  src.close(SaveOptions.DONOTSAVECHANGES);
  app.activeDocument = doc;
  doc.activeLayer.name = L.name;
}
var o = new PhotoshopSaveOptions(); o.layers = true; o.embedColorProfile = true;
doc.saveAs(new File(root.fsName + "/Cicek_Katmanli.psd"), o, true, Extension.LOWERCASE);
