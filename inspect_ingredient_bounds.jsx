var src = new File("C:/Users/joann/Downloads/FINALL pouch design(1) - vector gaps fixed.ai");
var log = new File("C:/Users/joann/Downloads/ClauseGaurd-main/ingredient-bounds-report.txt");
var doc = app.open(src);
var rows = [];

function fmt(b) {
    return "[" + Math.round(b[0]) + "," + Math.round(b[1]) + "," + Math.round(b[2]) + "," + Math.round(b[3]) + "]";
}

function isWhite(c) {
    try {
        if (c.typename === "RGBColor") return c.red > 245 && c.green > 245 && c.blue > 245;
        if (c.typename === "CMYKColor") return c.cyan < 4 && c.magenta < 4 && c.yellow < 4 && c.black < 4;
        if (c.typename === "GrayColor") return c.gray > 96;
    } catch (e) {}
    return false;
}

function colorName(c) {
    try {
        if (c.typename === "RGBColor") return "RGB " + Math.round(c.red) + "," + Math.round(c.green) + "," + Math.round(c.blue);
        if (c.typename === "CMYKColor") return "CMYK " + Math.round(c.cyan) + "," + Math.round(c.magenta) + "," + Math.round(c.yellow) + "," + Math.round(c.black);
        if (c.typename === "GrayColor") return "GRAY " + Math.round(c.gray);
        return c.typename;
    } catch (e) {}
    return "?";
}

function walk(item, groupName) {
    if (item.typename === "PathItem") {
        try {
            if (item.filled && !item.clipping && !item.guides && !isWhite(item.fillColor)) {
                rows.push(groupName + "\t" + fmt(item.visibleBounds) + "\t" + colorName(item.fillColor));
            }
        } catch (e) {}
        return;
    }
    try {
        for (var i = 0; i < item.pageItems.length; i++) walk(item.pageItems[i], groupName);
    } catch (e) {}
}

for (var li = 0; li < doc.layers.length; li++) {
    var layer = doc.layers[li];
    for (var gi = 0; gi < layer.groupItems.length; gi++) {
        var group = layer.groupItems[gi];
        var n = (group.name || "").toLowerCase();
        if (n.indexOf("leaves") >= 0 || n.indexOf("turmeric") >= 0 || n.indexOf("bowl") >= 0 || n.indexOf("haldi") >= 0) {
            walk(group, group.name);
        }
    }
}

log.open("w");
log.writeln("count=" + rows.length);
for (var r = 0; r < rows.length && r < 300; r++) log.writeln(rows[r]);
log.close();
doc.close(SaveOptions.DONOTSAVECHANGES);
