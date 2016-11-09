import ih.imgproc

plant = ih.imgproc.Image("/path/to/your/image")
plant.save("base")

logicList = [
"(((r + g) + b) > 350)",
"(r >= 250)",
"((b > 150) and (b < 220))",
"((((b max g) max r) - ((b min g) min r)) > 20)",
"((((r + g) + b) > 700) or (((r + g) + b) < 100))",
"((r - g) > 50)",
"(((g - r) > 15) and (b < g))"
]

for logic in logicList:
	plant.restore("base")
	plant.show("base")
	plant.colorFilter(logic)
	plant.show(logic)
	plant.wait()

