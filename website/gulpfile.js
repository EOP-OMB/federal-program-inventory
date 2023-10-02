/**
* Compile USWDS
*/
const uswds = require("@uswds/compile");

uswds.settings.version = 3;

uswds.paths.dist.img = "./_site/assets/img";
uswds.paths.dist.fonts = "./_site/assets/fonts";
uswds.paths.dist.js	= "./_site/assets/js";
uswds.paths.dist.css = "./_site/assets/css";

exports.updateUswds = uswds.updateUswds;