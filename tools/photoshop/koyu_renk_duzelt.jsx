#target photoshop
// Aktif Multichannel belgedeki 5 kanali (beyaz zemin + 4 murekkep) Spot Color yapar ve mürekkep renklerini atar.
app.displayDialogs = DialogModes.NO;
var doc = app.activeDocument;
var rgb = [[255,255,255],[231,47,15],[59,113,158],[9,43,121],[24,25,47]];
var show = [false, true, true, true, true];
for (var i = 0; i < doc.channels.length && i < rgb.length; i++) {
  var ch = doc.channels[i];
  if (i > 0) { try { ch.kind = ChannelType.SPOTCOLOR; } catch (e) {} }
  try {
    var c = new SolidColor();
    c.rgb.red = rgb[i][0]; c.rgb.green = rgb[i][1]; c.rgb.blue = rgb[i][2];
    ch.color = c;
  } catch (e) {}
  try { ch.opacity = 100; } catch (e) {}
}
for (var j = 0; j < doc.channels.length && j < show.length; j++) {
  try { doc.channels[j].visible = show[j]; } catch (e) {}
}
