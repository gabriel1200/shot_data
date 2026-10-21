python ~/basketball/nb2py.py get_min.ipynb

python ~/basketball/nb2py.py cluster/cluster2_scrape.ipynb
python ~/basketball/nb2py.py distance/set_distance.ipynb
#jupyter nbconvert --to script roles.ipynb
python ~/basketball/nb2py.py gen_opp.ipynb


python get_min.py
#python cluster/cluster2_scrape.py  

(cd distance && python set_distance.py)
python gen_opp.py
python ~/basketball/nb2py.py series/set_series_improved.ipynb

(cd series && python set_series_improved.py)
cp series/series_index.csv  ../web_app/data/series_index.csv
#python roles.py
#python gen_opp.py