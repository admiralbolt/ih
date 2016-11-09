import ih.imgproc

# base plant
plant = ih.imgproc.Image("0_0_2.png")
plant.save("base")
plant.show("base")

# blur
plant.blur((5, 5))
plant.save("blur")
plant.show("Blur")

# meanshift
plant.meanshift(4, 4, 40)
plant.save("shift")
plant.show("Meanshift")

# colorFilter
plant.colorFilter("(((g > r) and (g > b)) and (((r + g) + b) < 400))")
plant.colorFilter("(((r max g) max b) - ((r min g) min b)) > 12)")
plant.save("cf")
plant.show("Color filter")

# contourCut
plant.contourCut("cf", basemin = 3000, resize = True)
plant.save("cut")
plant.show("Contour Cut")

# recolor
plant.convertColor("bgr", "gray")
plant.threshold(0)
plant.convertColor("gray", "bgr")
plant.bitwise_and("base")
plant.write("final.png")
plant.show("Final")

print plant.extractPixels()
print plant.extractConvexHull()

plant.wait()
