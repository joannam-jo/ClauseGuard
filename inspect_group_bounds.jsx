var src = new File("C:/Users/joann/Downloads/FINALL pouch design(1) - vector gaps fixed.ai");
var log = new File("C:/Users/joann/Downloads/ClauseGaurd-main/group-bounds-report.txt");
var doc = app.open(src);

function fmt(b) {
    return "[" + Math.round(b[0]) + "," + Math.round(b[1]) + "," + Math.round(b[2]) + "," + Math.round(b[3]) + "]";
}

log.open("w");
for (var li = 0; li < doc.layers.length; li++) {
    var layer = doc.layers[li];
    log.writeln("LAYER\t" + li + "\t" + layer.name);
    for (var gi = 0; gi < layer.groupItems.length; gi++) {
        var g = layer.groupItems[gi];
        try {
            log.writeln("GROUP\t" + gi + "\t" + g.name + "\tvisible=" + fmt(g.visibleBounds) + "\tgeometric=" + fmt(g.geometricBounds));
        } catch (e) {}
    }
}
log.close();
doc.close(SaveOptions.DONOTSAVECHANGES);
