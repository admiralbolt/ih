import ih.imgproc

plant = ih.imgproc.Image("/path/to/your/image")

plant.crop([0, "y - 210", 0, "x"])
plant.write("crop.png")

plant.colorFilter("(g > 200)")
plant.write("thresh.png")

plant.contourChop(plant.image, 300)
plant.write("chop.png")

plant.contourCut(plant.image, resize = True)
plant.write("final.png")
