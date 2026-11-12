var src = new File("C:/Users/joann/Downloads/FINALL pouch design(1) - vector gaps fixed.ai");
var dest = new File("C:/Users/joann/Downloads/FINALL pouch design(1) - vector gaps fixed v2.ai");
var log = new File("C:/Users/joann/Downloads/ClauseGaurd-main/vector-gap-fill-pass2-log.txt");

var doc = app.open(src);
var changed = 0;
var groupsTouched = 0;
var whiteSkipped = 0;

function isWhite(c) {
    try {
        if (c.typename === "RGBColor") return c.red > 245 && c.green > 245 && c.blue > 245;
        if (c.typename === "CMYKColor") return c.cyan < 4 && c.magenta < 4 && c.yellow < 4 && c.black < 4;
        if (c.typename === "GrayColor") return c.gray > 96;
    } catch (e) {}
    return false;
}

function isNoColor(c) {
    try { return c.typename === "NoColor"; } catch (e) {}
    return false;
}

function boundsIntersect(a, b) {
    return !(a[2] < b[0] || a[0] > b[2] || a[3] > b[1] || a[1] < b[3]);
}

function shouldTouchBounds(b) {
    // Ingredient art zones from the pouch: left leaf column and lower turmeric/bowl image.
    var zones = [
        [20, 760, 215, 145],
        [10, 230, 430, 10]
    ];
    for (var i = 0; i < zones.length; i++) {
        if (boundsIntersect(b, zones[i])) return true;
    }
    return false;
}

function repairPath(p) {
    try {
        if (p.guides || p.clipping || p.locked || p.hidden) return;
        if (!p.filled || isNoColor(p.fillColor)) return;
        if (isWhite(p.fillColor)) {
            whiteSkipped++;
            return;
        }
        if (!shouldTouchBounds(p.visibleBounds)) return;

        p.stroked = true;
        p.strokeColor = p.fillColor;
        p.strokeWidth = 2.8;
        p.strokeJoin = StrokeJoin.ROUNDENDJOIN;
        p.strokeCap = StrokeCap.ROUNDENDCAP;
        changed++;
    } catch (e) {}
}

function repairItem(item) {
    if (item.typename === "PathItem") {
        repairPath(item);
        return;
    }
    try {
        for (var i = 0; i < item.pageItems.length; i++) repairItem(item.pageItems[i]);
    } catch (e) {}
}

function nameSuggestsIngredient(n) {
    n = (n || "").toLowerCase();
    return n.indexOf("leaves") >= 0 ||
        n.indexOf("turmeric") >= 0 ||
        n.indexOf("bowl") >= 0 ||
        n.indexOf("haldi") >= 0;
}

for (var li = 0; li < doc.layers.length; li++) {
    var layer = doc.layers[li];
    if (layer.locked || !layer.visible) continue;
    for (var gi = 0; gi < layer.groupItems.length; gi++) {
        var group = layer.groupItems[gi];
        if (nameSuggestsIngredient(group.name)) {
            groupsTouched++;
            repairItem(group);
        }
    }
}

if (groupsTouched === 0) {
    for (var li2 = 0; li2 < doc.layers.length; li2++) {
        var layer2 = doc.layers[li2];
        if (layer2.locked || !layer2.visible) continue;
        repairItem(layer2);
    }
}

var saveOpts = new IllustratorSaveOptions();
saveOpts.pdfCompatible = true;
saveOpts.embedICCProfile = true;
saveOpts.compressed = true;
doc.saveAs(dest, saveOpts);

for (var a = 0; a < doc.artboards.length; a++) {
    doc.artboards.setActiveArtboardIndex(a);
    var out = new File("C:/Users/joann/Downloads/ClauseGaurd-main/gaps-fixed-v2-artboard-" + (a + 1) + ".png");
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
log.writeln("groupsTouched=" + groupsTouched);
log.writeln("coloredPathsRepaired=" + changed);
log.writeln("whitePathsSkipped=" + whiteSkipped);
log.writeln("strokeWidthPt=2.8");
log.close();

doc.close(SaveOptions.DONOTSAVECHANGES);
