var src = new File("C:/Users/joann/Downloads/FINALL pouch design(1) - vector gaps fixed.ai");
var dest = new File("C:/Users/joann/Downloads/FINALL pouch design(1) - clean vector underlay v4.ai");
var log = new File("C:/Users/joann/Downloads/ClauseGaurd-main/clean-underlay-v4-log.txt");

var doc = app.open(src);
var added = 0;

function green(c, m, y, k) {
    var col = new CMYKColor();
    col.cyan = c;
    col.magenta = m;
    col.yellow = y;
    col.black = k;
    return col;
}

function addBlob(parent, pts, fill, opacity) {
    var p = parent.pathItems.add();
    p.setEntirePath(pts);
    p.closed = true;
    p.filled = true;
    p.fillColor = fill;
    p.stroked = false;
    p.opacity = opacity;
    try {
        for (var i = 0; i < p.pathPoints.length; i++) {
            p.pathPoints[i].pointType = PointType.SMOOTH;
        }
    } catch (e) {}
    try { p.zOrder(ZOrderMethod.SENDTOBACK); } catch (e2) {}
    added++;
    return p;
}

function nameSuggestsIngredient(n) {
    n = (n || "").toLowerCase();
    return n.indexOf("leaves") >= 0 || n.indexOf("turmeric") >= 0 || n.indexOf("bowl") >= 0 || n.indexOf("haldi") >= 0;
}

function repairGroup(g) {
    var b = g.visibleBounds;
    var left = b[0], top = b[1], right = b[2], bottom = b[3];
    var w = right - left;
    var h = top - bottom;
    var base = green(78, 18, 100, 24);
    var dark = green(86, 38, 96, 42);
    var light = green(55, 4, 95, 0);

    if (right < 0) {
        // Left artboard: clean connectors behind top, middle, and lower leaf clusters.
        addBlob(g, [
            [left + w * 0.20, top - h * 0.03],
            [right + 4, top - h * 0.02],
            [right + 6, top - h * 0.30],
            [left + w * 0.42, top - h * 0.36],
            [left + w * 0.10, top - h * 0.24]
        ], base, 100);
        addBlob(g, [
            [left + w * 0.24, top - h * 0.30],
            [right + 5, top - h * 0.36],
            [right + 5, top - h * 0.54],
            [left + w * 0.39, top - h * 0.60],
            [left + w * 0.12, top - h * 0.50]
        ], light, 96);
        addBlob(g, [
            [left + w * 0.10, bottom + h * 0.38],
            [right + 5, bottom + h * 0.42],
            [right + 6, bottom + h * 0.06],
            [left + w * 0.34, bottom - 4],
            [left + w * 0.05, bottom + h * 0.15]
        ], base, 100);
        addBlob(g, [
            [right - w * 0.36, top - h * 0.02],
            [right + 8, top - h * 0.01],
            [right + 8, bottom + h * 0.02],
            [right - w * 0.22, bottom + h * 0.08],
            [right - w * 0.26, top - h * 0.42]
        ], dark, 94);
    } else {
        // Right artboard equivalent.
        addBlob(g, [
            [left + w * 0.16, top - h * 0.03],
            [right + 4, top - h * 0.03],
            [right + 6, top - h * 0.35],
            [left + w * 0.38, top - h * 0.40],
            [left + w * 0.07, top - h * 0.25]
        ], base, 100);
        addBlob(g, [
            [left + w * 0.08, bottom + h * 0.38],
            [right + 5, bottom + h * 0.43],
            [right + 7, bottom + h * 0.04],
            [left + w * 0.34, bottom - 4],
            [left + w * 0.02, bottom + h * 0.16]
        ], base, 100);
        addBlob(g, [
            [right - w * 0.30, top - h * 0.01],
            [right + 8, top - h * 0.01],
            [right + 8, bottom + h * 0.03],
            [right - w * 0.18, bottom + h * 0.10],
            [right - w * 0.22, top - h * 0.48]
        ], dark, 94);
    }
}

var touched = 0;
for (var li = 0; li < doc.layers.length; li++) {
    var layer = doc.layers[li];
    if (layer.locked || !layer.visible) continue;
    for (var gi = 0; gi < layer.groupItems.length; gi++) {
        var g = layer.groupItems[gi];
        if (nameSuggestsIngredient(g.name)) {
            repairGroup(g);
            touched++;
        }
    }
}

var saveOpts = new IllustratorSaveOptions();
saveOpts.pdfCompatible = true;
saveOpts.embedICCProfile = true;
saveOpts.compressed = true;
doc.saveAs(dest, saveOpts);

for (var a = 0; a < doc.artboards.length; a++) {
    doc.artboards.setActiveArtboardIndex(a);
    var out = new File("C:/Users/joann/Downloads/ClauseGaurd-main/clean-underlay-v4-artboard-" + (a + 1) + ".png");
    var o = new ExportOptionsPNG24();
    o.antiAliasing = true;
    o.artBoardClipping = true;
    o.transparency = false;
    o.horizontalScale = 250;
    o.verticalScale = 250;
    doc.exportFile(out, ExportType.PNG24, o);
}

log.open("w");
log.writeln("source=" + src.fsName);
log.writeln("output=" + dest.fsName);
log.writeln("ingredientGroupsTouched=" + touched);
log.writeln("cleanUnderlayShapesAdded=" + added);
log.close();

doc.close(SaveOptions.DONOTSAVECHANGES);
