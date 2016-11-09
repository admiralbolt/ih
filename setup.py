from distutils.core import setup

setup(
	name="ih",
	version="1.0",
	packages=["ih"],
	license="GPL",
	scripts=[
		"scripts/ih-bitwise-and",
		"scripts/ih-bitwise-not",
		"scripts/ih-bitwise-or",
		"scripts/ih-bitwise-xor",
		"scripts/ih-convert-color",
		"scripts/ih-meanshift",
		"scripts/ih-threshold",
		"scripts/ih-extract",
		"scripts/ih-adaptive-threshold",
		"scripts/ih-blur",
		"scripts/ih-gaussian-blur",
		"scripts/ih-median-blur",
		"scripts/ih-normalize-intensity",
		"scripts/ih-morphology",
		"scripts/ih-crop",
		"scripts/ih-fill",
		"scripts/ih-contour-cut",
		"scripts/ih-contour-chop",
		"scripts/ih-edges",
		"scripts/ih-color-filter",
		"scripts/ih-resize",
        "scripts/ih-mask",
		"scripts/ih-add-weighted",
		"scripts/ih-split",
		"scripts/ih-equalize-hist",
		"scripts/ih-flood-fill",

		"scripts/ih-seed",
        "scripts/ih-write-sql",

		"scripts/ih-setup",
		"scripts/ih-crawl",
		"scripts/ih-run",
		"scripts/ih-error-log",
		"scripts/ih-extract-all",
		"scripts/ih-extract-multi",
		"scripts/ih-sql-aggregate",
		"scripts/osg-wrapper.sh",

		"scripts/ih-data",


		"scripts/ih-stats-shoot-area",
		"scripts/ih-stats-normalize",
		"scripts/ih-stats-correlate",
		"scripts/ih-stats-threshold",
		"scripts/ih-stats-anova",
		"scripts/ih-stats-treatment-comp",
		"scripts/ih-stats-ttest",
		"scripts/ih-stats-histogram-bin",
		"scripts/ih-stats-export"
	]
)
