import ih.imgproc

plant = ih.imgproc.Image("/path/to/your/image")

plant.crop([280, "y - 175", 1000, 3200])
plant.write("crop.png")

plant.colorFilter("((g - b) > 0)")
plant.write("thresh.png")

plant.contourChop(plant.image, 1000)
plant.write("chop.png")

plant.contourCut(plant.image, resize = True)
plant.write("final.png")
