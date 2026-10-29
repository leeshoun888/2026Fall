set -e
cd ~/Documents/boramal-geo-midterm-2026/film
P3="Cinematic film still, the same two real Korean brothers from the reference images (preserve their exact faces), working late at night in their small startup studio. The older brother with clear thin-rimmed glasses in a deep violet-navy shirt stands and points at a monitor full of structured data tables, the younger brother in a lavender-purple hoodie sits typing on a keyboard beside him, purple and soft white practical lights, dual monitors glowing, focused determined expressions, both faces clearly visible in three-quarter view, medium shot, 35mm film look, photorealistic, screens show abstract blurred data, no readable text."
P7="Cinematic wide film still at dawn, the same two real Korean brothers from the reference images (preserve their exact faces) standing on a Seoul rooftop looking out over the city skyline as the sun rises, soft purple and orange sky, older brother with clear thin-rimmed glasses in a deep violet-navy shirt and younger brother in a lavender-purple hoodie, three-quarter view from slightly behind with both faces visible and smiling, hopeful mood, wind in hair, anamorphic lens flare, photorealistic, no text."
REFS="--image-references keyframes/char_real.png --image-references real_photos/ref_both_1.jpg --image-references real_photos/ref_soun.jpg"
gen() { higgsfield generate create gpt_image_2_5 --prompt "$2" $REFS --aspect_ratio 16:9 --resolution 2k --quality high --wait --wait-timeout 15m --json > keyframes/$1r.json
  curl -s -o keyframes/$1r.png "$(python3 -c "import json;print(json.load(open('keyframes/$1r.json'))[0]['result_url'])")"; sips -Z 1000 keyframes/$1r.png --out keyframes/$1r_prev.jpg -s format jpeg >/dev/null; }
gen k3 "$P3" & gen k7 "$P7" & wait
echo images done
