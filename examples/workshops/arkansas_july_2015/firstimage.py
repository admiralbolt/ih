# Load the library & image
import ih.imgproc
plant = ih.imgproc.Image("/path/to/your/image")
# Save & show the base image
plant.save("base")
plant.show("Base")
# Convert to gray, save the image
plant.convertColor("bgr", "gray")
plant.save("gray")
plant.show("Grayscale")
# Threshold the image incorrectly AND correctly
plant.threshold(255)
plant.show("Threshold 255")
plant.restore("gray")
plant.threshold(190)
plant.save("binary")
plant.show("Threshold 190")
# Recolor the image
plant.bitwise_not()
plant.convertColor("gray", "bgr")
plant.bitwise_and("base")
plant.save("recolor")
plant.show("Recolored Image")
# Crop the image, produce the final output
plant.crop([300, 2150, 0, "x"])
plant.save("cropped")
plant.show("Cropped")
plant.contourCut("cropped", resize = True)
plant.show("Final")
plant.write("final.png")
plant.wait()
