#target photoshop
// Betikle ayni klasordeki katmanlar.json + PNG'lerden her nesne ayri katman olacak sekilde PSD uretir ve ayni klasore kaydeder.
app.displayDialogs = DialogModes.NO;
app.preferences.rulerUnits = Units.PIXELS;
var root = new File($.fileName).parent;
var jf = new File(root.fsName + "/katmanlar.json"); jf.encoding = "UTF-8"; jf.open("r");
var meta = eval("(" + jf.read() + ")"); jf.close();
var doc = app.documents.add(meta.W, meta.H, meta.ppi, "Katmanli_Yazi_Top", NewDocumentMode.RGB, DocumentFill.WHITE);
doc.activeLayer.name = "Zemin (beyaz)";
for (var i = 0; i < meta.layers.length; i++) {
  var L = meta.layers[i];
  var src = app.open(new File(root.fsName + "/" + L.file));
  src.selection.selectAll(); src.selection.copy();
  src.close(SaveOptions.DONOTSAVECHANGES);
  app.activeDocument = doc;
  doc.paste();
  var lyr = doc.activeLayer; lyr.name = L.name;
  var b = lyr.bounds;
  lyr.translate(L.x - b[0].as("px"), L.y - b[1].as("px"));
}
var o = new PhotoshopSaveOptions(); o.layers = true; o.embedColorProfile = true;
doc.saveAs(new File(root.fsName + "/Katmanli_Yazi_Top.psd"), o, true, Extension.LOWERCASE);
