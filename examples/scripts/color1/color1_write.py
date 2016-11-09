import ih.imgproc

plant = ih.imgproc.Image("/Users/aknecht/git/ih/docs/images/sample/rgbtv1_small.png")
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

for i,logic in enumerate(logicList):
	plant.restore("base")
	plant.colorFilter(logic)
	plant.write("logic" + str(i) + ".png")

