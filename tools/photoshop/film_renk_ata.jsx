#target photoshop
// Aktif Multichannel belgede kanallari Spot Color yapar ve renkleri kanallar_hibrit.json'dan atar.
// Json'u bulamazsa klasor secme penceresi acar.
app.displayDialogs = DialogModes.NO;
var jf = new File(new File($.fileName).parent.fsName + "/kanallar_hibrit.json");
if (!jf.exists) jf = File.openDialog("kanallar_hibrit.json sec");
jf.encoding = "UTF-8"; jf.open("r"); var meta = eval("(" + jf.read() + ")"); jf.close();
var list = meta.sets.Acik_Tisort, doc = app.activeDocument;
for (var i = 0; i < doc.channels.length && i < list.length; i++) {
  var ch = doc.channels[i];
  try { ch.kind = ChannelType.SPOTCOLOR; } catch (e) {}
  try { var c = new SolidColor(); c.rgb.red = list[i][2][0]; c.rgb.green = list[i][2][1]; c.rgb.blue = list[i][2][2]; ch.color = c; } catch (e) {}
  try { ch.opacity = 100; } catch (e) {}
}
for (var j = 0; j < doc.channels.length; j++) { try { doc.channels[j].visible = true; } catch (e) {} }
