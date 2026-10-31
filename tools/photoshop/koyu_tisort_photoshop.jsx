#target photoshop
// Koyu_Tisort klasorundeki tramsiz 1-bit filmleri tek bir Multichannel belgede Spot Color kanallari olarak toplar.
app.displayDialogs = DialogModes.NO;
var base = new File($.fileName).parent.fsName + "/Koyu_Tisort";
var list = [
  ["01 Beyaz Zemin (underbase)", "01_Beyaz_Zemin.png", [255,255,255], false],
  ["02 Kırmızı",   "02_Kirmizi.png",     [231,47,15],   true],
  ["03 Mavi 2",                   "03_Mavi_2.png",      [59,113,158],  true],
  ["04 Mavi 1",                   "04_Mavi_1.png",      [9,43,121],    true],
  ["05 Siyah",                    "05_Siyah.png",       [24,25,47],    true]
];
function openGray(name) {
  var d = app.open(new File(base + "/" + name));
  if (d.mode == DocumentMode.BITMAP) d.changeMode(ChangeMode.GRAYSCALE);
  return d;
}
var target = openGray(list[0][1]);
target.changeMode(ChangeMode.MULTICHANNEL);
target.channels[0].name = list[0][0];
for (var i = 1; i < list.length; i++) {
  var src = openGray(list[i][1]);
  src.selection.selectAll(); src.selection.copy();
  src.close(SaveOptions.DONOTSAVECHANGES);
  app.activeDocument = target;
  var ch = target.channels.add();
  ch.name = list[i][0];
  target.activeChannels = [ch];
  target.paste();
  target.selection.deselect();
}
var log = [];
for (var k = 0; k < list.length; k++) {
  var c = target.channels[k], note = c.name + ": ";
  if (k > 0) { try { c.kind = ChannelType.SPOTCOLOR; note += "spot "; } catch (e) { note += "kind-HATA "; } }
  try { var col = new SolidColor(); col.rgb.red = list[k][2][0]; col.rgb.green = list[k][2][1]; col.rgb.blue = list[k][2][2]; c.color = col; note += "renk "; } catch (e) { note += "renk-HATA "; }
  try { c.opacity = 100; } catch (e) {}
  try { c.visible = list[k][3]; } catch (e) {}
  log.push(note);
}
alert(log.join("\n"));
