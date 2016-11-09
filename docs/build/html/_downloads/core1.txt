import ih.imgproc

plant = ih.imgproc.Image("/Volumes/BLOO/Work/hcc/ih/paper/fluosv/step0.png")

plant.save("base")
plant.show("base")
plant.write("base.png")

plant.convertColor("bgr", "gray")
plant.save("gray")
plant.show("gray")
plant.write("gray.png")

plant.threshold(50)
plant.save("thresh50")
plant.show("thresh50")
plant.restore("gray")

plant.threshold(75)
plant.save("thresh75")
plant.show("thresh75")
plant.restore("gray")

plant.threshold(100)
plant.save("thresh100")
plant.show("thresh100")
plant.restore("gray")

plant.wait()
plant.restore("thresh50")
plant.write("thresh50.png")
