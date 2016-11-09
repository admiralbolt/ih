Image Processing Viewer
========================

.. raw:: html

	<!-- <script type="text/javascript" src="/data/viewerim/viewer.json"></script> -->
    <script type="text/javascript" src="/Users/aknecht/git/ih/docs/images/viewer.json"></script>
	<script type="text/javascript">
		var base = "/Users/aknecht/git/ih/docs/images/";
        // var base = "/data/viewerim/"
		$(function() {
			$("#function").on("change", function() {
				optstr = ""
				if ($("#function").val() == "bitwise_not" || $("#function").val() == "normalizeByIntensity") {
					optstr += "<input type='hidden' class='imload' />";
				}
				for (var ordernum in data[$("#function").val()]["order"]) {
					option = data[$("#function").val()]["order"][ordernum]
					optstr += "<div class='form-group'>";
					optstr += "<label for='" + option + "'>" + option + "</label>";
					optstr += "<select class='form-control imload' name='" + option + "' id='load_" + ordernum + "'>";
					for (var arg in data[$("#function").val()][option]) {
						optstr += "<option value='" + data[$("#function").val()][option][arg] + "'>" + data[$("#function").val()][option][arg] + "</option>";
					}
					optstr += "</select>"
					optstr += "</div>";
				}
				$("#options").html(optstr);
				$("#options .imload").trigger("change");
			});
			$("#image").on("change", function() {
				$("#inputImage").html("<img src='" + base + "sample/" + $("#image").val() + "' />");
				$("#options .imload").trigger("change");
			});
			$("#options").on("change", ".imload", function() {
				var l = $("#options > div").length;
				var impath = base + "/" + $("#function").val() + "/"
				for (var i = 0; i < l; i++) {
					impath += $("#load_" + i).attr("name");
					impath += $("#load_" + i).val()
				}
				impath += $("#image").val();
				$("#outputImage").html("<img src='" + escape(impath) + "' />");
			});
			$("#function").trigger("change");
			$("#image").trigger("change");
		});
	</script>
	<div class="row">
		<div style="height:613px;" class="col-md-2">
			<form>
				<div class="form-group">
					<label for="function">Function</label>
					<select class="form-control" id="function">
						<option value="adaptiveThreshold">Adaptive Threshold</option>
						<option value="bitwise_and">Bitwise And</option>
						<option value="bitwise_not">Bitwise Not</option>
						<option value="bitwise_or">Bitwise Or</option>
						<option value="bitwise_xor">Bitwise XOr</option>
						<option value="blur">Blur</option>
						<option value="colorFilter">Color Filter</option>
						<option value="convertColor">Convert Color</option>
						<option value="crop">Crop</option>
						<option value="edges">Edges</option>
						<option value="gaussianBlur">Gaussian Blur</option>
						<option value="kmeans">Kmeans</option>
						<option value="meanshift">Mean Shift Segmentation</option>
						<option value="morphology">Morphology</option>
						<option value="normalizeByIntensity">Normalize By Intensity</option>
						<option value="threshold">Threshold</option>
					</select>
				</div>
				<div class="form-group">
					<label for="image">Images</label>
					<select class="form-control" id="image">
						<option value="rgbsv1.png">rgbsv1</option>
						<option value="rgbsv2.png">rgbsv2</option>
						<option value="rgbsv3.png">rgbsv3</option>
						<option value="rgbtv1.png">rgbtv1</option>
						<option value="rgbtv2.png">rgbtv2</option>
						<option value="rgbtv3.png">rgbtv3</option>
						<option value="fluosv1.png">fluosv1</option>
						<option value="fluosv2.png">fluosv2</option>
					</select>
				</div>
				<div class="form-group">
					<label for="options">Options</label>
					<hr style="margin-top:0px;margin-bottom:5px;">
				</div>
				<div id="options">
				
				</div>
			</form>
		</div>
		<div id="inputImage" style="height:613px;" class="col-md-5">
		
		</div>
		<div id="outputImage" style="height:613px;" class="col-md-5">
		
		</div>
	</div>
	<div class="row">
		<br />
	</div> 
	
