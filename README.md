# Nigeria Se4all Main Website including the Webmap 
Nigeria SE4ALL offers the most accurate data and latest tools that empower better electrification planning in Nigeria

## Public instances
- [Nigeria SE4ALL Website](https://nigeriase4all.gov.ng/)

## Financed By
- [Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ)](https://www.giz.de/)
- [Federal Ministry of Power, Works and Housing ](http://www.power.gov.ng)
- under the Nigerian Energy Support Programme
- (Co-funded) by the German Government and the European Union

## Authors and Developed By
- [INTEGRATION environment & energy](http://www.integration.org/)
- [Reiner Lemoine Institut gGmbH](www.reiner-lemoine-institut.de)
- [Alsino Skowronnek](www.alsino.io)

## Feature List:
- detailed project overview of nigerian rural electrification under the NESP
- Webmap on three different levels (national, state, villate) on rural electrification 
- fully dynamic filters on all datasets
- Ground-Truth electrification/building data  
- download all public datasets via a dedicated Geonode instance

## Architecture:
- Python/Flask 
- Leavelet
- Tilelayer setup with dedicated Tileserver
- Bootstrap

## Getting started

After cloning this repository, checkout the `dev` branch
```
git checkout dev
```

Create a virtual environment (with python3), then
```
pip3 install -r app/requirements.txt
```

Pull the latest changes from the [maps repository](https://github.com/rl-institut/NESP2)
```
python3 app/setup_maps.py
```

Start the app with  
```
python3 index.py
```
