var src = new File("C:/Users/joann/Downloads/FINALL pouch design(1).ai");
var dest = new File("C:/Users/joann/Downloads/ClauseGaurd-main/FINALL pouch design(1) - vector gaps fixed.ai");
var log = new File("C:/Users/joann/Downloads/ClauseGaurd-main/vector-gap-fill-log.txt");

var doc = app.open(src);
var changed = 0;
var whiteSkipped = 0;
var groupsTouched = 0;

function isWhite(c) {
    try {
        if (c.typename === "RGBColor") return c.red > 246 && c.green > 246 && c.blue > 246;
        if (c.typename === "CMYKColor") return c.cyan < 3 && c.magenta < 3 && c.yellow < 3 && c.black < 3;
        if (c.typename === "GrayColor") return c.gray > 97;
    } catch (e) {}
    return false;
}

function isTransparentLike(c) {
    try {
        return c.typename === "NoColor";
    } catch (e) {}
    return false;
}

function colorKey(c) {
    try {
        if (c.typename === "RGBColor") return "rgb(" + Math.round(c.red) + "," + Math.round(c.green) + "," + Math.round(c.blue) + ")";
        if (c.typename === "CMYKColor") return "cmyk(" + Math.round(c.cyan) + "," + Math.round(c.magenta) + "," + Math.round(c.yellow) + "," + Math.round(c.black) + ")";
        if (c.typename === "GrayColor") return "gray(" + Math.round(c.gray) + ")";
    } catch (e) {}
    return "unknown";
}

function shouldRepairPath(p) {
    try {
        if (p.guides || p.clipping || p.locked || p.hidden) return false;
        if (!p.filled || isTransparentLike(p.fillColor)) return false;
        if (isWhite(p.fillColor)) {
            whiteSkipped++;
            return false;
        }
        return true;
    } catch (e) {
        return false;
    }
}

function repairPath(p, width) {
    try {
        p.stroked = true;
        p.strokeColor = p.fillColor;
        p.strokeWidth = width;
        p.strokeJoin = StrokeJoin.ROUNDENDJOIN;
        p.strokeCap = StrokeCap.ROUNDENDCAP;
        changed++;
    } catch (e) {}
}

function repairItem(item, depth) {
    if (item.typename === "PathItem") {
        if (shouldRepairPath(item)) {
            var w = 1.2;
            try {
                var k = colorKey(item.fillColor);
                if (k.indexOf("rgb(0,") === 0 || k.indexOf("cmyk(") === 0) w = 1.6;
            } catch (e) {}
            repairPath(item, w);
        }
        return;
    }

    try {
        for (var i = 0; i < item.pageItems.length; i++) repairItem(item.pageItems[i], depth + 1);
    } catch (e) {}
}

function nameSuggestsTarget(n) {
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
        if (nameSuggestsTarget(group.name)) {
            groupsTouched++;
            repairItem(group, 0);
        }
    }
}

if (groupsTouched === 0) {
    for (var li2 = 0; li2 < doc.layers.length; li2++) {
        var layer2 = doc.layers[li2];
        if (layer2.locked || !layer2.visible) continue;
        repairItem(layer2, 0);
    }
}

var saveOpts = new IllustratorSaveOptions();
saveOpts.pdfCompatible = true;
saveOpts.embedICCProfile = true;
saveOpts.compressed = true;
doc.saveAs(dest, saveOpts);

for (var a = 0; a < doc.artboards.length; a++) {
    doc.artboards.setActiveArtboardIndex(a);
    var out = new File("C:/Users/joann/Downloads/ClauseGaurd-main/gaps-fixed-artboard-" + (a + 1) + ".png");
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
log.writeln("strokeWidthPt=1.2-1.6");
log.close();

doc.close(SaveOptions.DONOTSAVECHANGES);
