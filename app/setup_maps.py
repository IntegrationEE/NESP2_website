import os
import argparse
from shutil import copyfile, rmtree

cur_dir = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser(prog="setup_maps", description="Merge the NESP2 maps repository")
parser.add_argument(
    "-docker",
    dest="docker",
    help="specify if the file is run from docker",
    nargs="?",
    const=True,
    default=False,
    type=bool,
)
args = parser.parse_args()

if args.docker is False:
    # clone the NESP2 repository locally
    branch = 'dev'
    if os.path.exists('NESP2') is False:
        os.system(
            "git clone --single-branch --branch {} https://github.com/rl-institut/NESP2.git".format(
                branch
            )
        )

# copy templates
template_path = os.path.join('NESP2', 'app', 'templates')

new_template_path = os.path.join('app', 'templates', 'maps')

if os.path.exists(new_template_path) is False:
    os.mkdir(new_template_path)

for fname in os.listdir(template_path):
    if fname not in ('base.html'):
        copyfile(os.path.join(template_path, fname), os.path.join(new_template_path, fname))
    if fname == 'base.html':
        copyfile(os.path.join(template_path, fname), os.path.join(new_template_path, 'maps_{}'.format(fname)))

# copy python files
app_path = os.path.join('NESP2', 'app')

new_app_path = os.path.join('app')

for fname in os.listdir(app_path):
    if fname in ('utils.py'):
        copyfile(os.path.join(app_path, fname), os.path.join(new_app_path, 'maps_{}'.format(fname)))

# copy static files
static_path = os.path.join('NESP2', 'app', 'static')

new_static_path = os.path.join('app', 'static')

static_types = ['data', 'images', 'css', 'js']
new_static_types = {'data': 'data', 'images': os.path.join('img', 'maps'), 'css': 'css', 'js': 'js'}

for static_type in static_types:
    new_static_type = new_static_types[static_type]

    # create the folder if it does not exists
    if os.path.exists(os.path.join(new_static_path, new_static_type)) is False:
        os.mkdir(os.path.join(new_static_path, new_static_type))

    # copy the files from NESP2 repo the folder of NESP2 template
    for fname in os.listdir(os.path.join(static_path, static_type)):
        if fname not in ('local.css', 'jquery-3.4.1.min.js'):
            copyfile(
                os.path.join(static_path, static_type, fname),
                os.path.join(new_static_path, new_static_type, fname)
            )



# erase the NESP2 repository
rmtree(os.path.join('NESP2'))

if args.docker is True:
    print("Succesfully setup the NESP2 maps")