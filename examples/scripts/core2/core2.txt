import ih.imgproc

plant = ih.imgproc.Image("/path/to/your/image")

plant.save("base")
plant.show("base")
plant.write("base.png")

plant.convertColor("bgr", "gray")
plant.show("grayscale")
plant.write("gray.png")

plant.gaussianBlur((5, 5))
plant.show("blur")
plant.write("blur.png")

plant.adaptiveThreshold(255, "mean", "binary", 15, 3)
plant.show("adaptive threshold")
plant.write("thresh.png")

plant.bitwise_not()
plant.show("invert")
plant.write("invert.png")

plant.convertColor("gray", "bgr")
plant.bitwise_and("base")
plant.show("recolor")
plant.write("recolor.png")

plant.morphology("open", "rect", (3, 3))
plant.show("morph")
plant.write("morph.png")

plant.colorFilter("(((max - min) > 40) and ((b - g) < 30))", [plant.y - 350, plant.y, -1, -1])
plant.show("filter")
plant.write("filter.png")
plant.save("filter")

plant.convertColor("bgr", "gray")
plant.threshold(0)
plant.save("binary")
plant.restore("filter")

plant.contourCut("binary", basemin = 500, resize = True)
plant.show("final")
plant.write("final.png")

print "total plant pixels = ",plant.extractPixels()
print "[plant height, plant width] = ",plant.extractDimensions()
print "Nonzero color data -- [ [bmean, bmed], [gmean, gmed], [rmean, rmed] ] = ",plant.extractColorData()
print "With zero color data -- [ [bmean, bmed], [gmean, gmed], [rmean, rmed] ] = ",plant.extractColorData(nonzero = False)
plant.wait()
