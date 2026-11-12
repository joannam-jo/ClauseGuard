var src = new File("C:/Users/joann/Downloads/FINALL pouch design copy.ai");
var report = new File("C:/Users/joann/Downloads/ClauseGaurd-main/artwork-report.txt");
var doc = app.open(src);
for (var a = 0; a < doc.artboards.length; a++) {
  doc.artboards.setActiveArtboardIndex(a);
  var out = new File("C:/Users/joann/Downloads/ClauseGaurd-main/artboard-" + (a + 1) + ".png");
  var opts = new ExportOptionsPNG24();
  opts.antiAliasing = true; opts.artBoardClipping = true; opts.transparency = false;
  opts.horizontalScale = 250; opts.verticalScale = 250;
  doc.exportFile(out, ExportType.PNG24, opts);
}
report.open("w");
report.writeln("name=" + doc.name); report.writeln("artboards=" + doc.artboards.length); report.writeln("layers=" + doc.layers.length); report.writeln("pageItems=" + doc.pageItems.length);
for (var i=0;i<doc.layers.length;i++){var layer=doc.layers[i];report.writeln("layer["+i+"]="+layer.name+"; visible="+layer.visible+"; locked="+layer.locked+"; items="+layer.pageItems.length);}
report.close(); doc.close(SaveOptions.DONOTSAVECHANGES); app.quit();
