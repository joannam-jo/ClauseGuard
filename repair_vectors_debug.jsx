var errFile=new File("C:/Users/joann/Downloads/ClauseGaurd-main/vector-repair-error.txt");try{
var src=new File("C:/Users/joann/Downloads/FINALL pouch design copy.ai");
var dest=new File("C:/Users/joann/Downloads/ClauseGaurd-main/FINALL pouch design copy - joined vectors.ai");
var log=new File("C:/Users/joann/Downloads/ClauseGaurd-main/vector-repair-log.txt");
var doc=app.open(src); var changed=0, groups=0, skippedWhite=0;
function isWhite(c){try{if(c.typename==="RGBColor")return c.red>248&&c.green>248&&c.blue>248;if(c.typename==="CMYKColor")return c.cyan<2&&c.magenta<2&&c.yellow<2&&c.black<2;if(c.typename==="GrayColor")return c.gray>98;}catch(e){}return false;}
function trapItem(item){if(item.typename==="PathItem"){try{if(item.filled&&!item.clipping&&!item.guides&&!isWhite(item.fillColor)){item.stroked=true;item.strokeColor=item.fillColor;item.strokeWidth=0.6;item.strokeJoin=StrokeJoin.ROUNDENDJOIN;changed++;}else if(item.filled&&isWhite(item.fillColor)){skippedWhite++;}}catch(e){}} else {try{for(var k=0;k<item.pageItems.length;k++)trapItem(item.pageItems[k]);}catch(e){}}}
for(var li=0;li<doc.layers.length;li++){var L=doc.layers[li];for(var i=0;i<L.groupItems.length;i++){var g=L.groupItems[i];if(g.name==="leaves-and-turmeric-bowl"){groups++;trapItem(g);}}}
var saveOpts=new IllustratorSaveOptions();saveOpts.pdfCompatible=true;saveOpts.embedICCProfile=true;saveOpts.compressed=true;doc.saveAs(dest,saveOpts);
for(var a=0;a<doc.artboards.length;a++){doc.artboards.setActiveArtboardIndex(a);var out=new File("C:/Users/joann/Downloads/ClauseGaurd-main/repaired-artboard-"+(a+1)+".png");var o=new ExportOptionsPNG24();o.antiAliasing=true;o.artBoardClipping=true;o.transparency=false;o.horizontalScale=250;o.verticalScale=250;doc.exportFile(out,ExportType.PNG24,o);}
log.open("w");log.writeln("targetGroups="+groups);log.writeln("coloredPathsTrapped="+changed);log.writeln("whitePathsSkipped="+skippedWhite);log.writeln("strokeWidthPt=0.6");log.close();doc.close(SaveOptions.DONOTSAVECHANGES);
}catch(e){errFile.open("w");errFile.writeln(e+" line="+e.line);errFile.close();try{app.activeDocument.close(SaveOptions.DONOTSAVECHANGES);}catch(x){}}