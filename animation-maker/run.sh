#! /bin/bash
set -e

# Variables to change
odb_filename="/volume/NFS/cf511/beegfs/mod_2e-01_str_ratio_4e-01_seed_6002.odb"
field_output="CSDMG    General_Contact_Faces/General_Contact_Faces" # from abaqus
label="CSDMG"                                                       # will show on the side of the plot

/usr/local/DassaultSystemes/Commands/abaqus python -u odb_data_saver.py "$odb_filename" "$field_output"
python3 -u plot_maker.py $label
echo "Starting ffmpeg"
ffmpeg -i frame_%01d.png -pix_fmt yuv420p -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2' -f mp4 animation.mp4 -y
