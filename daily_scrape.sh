jupyter nbconvert --to script get_min.ipynb

#jupyter nbconvert --to script cluster/cluster2_scrape.ipynb
jupyter nbconvert --to script distance/set_distance.ipynb
#jupyter nbconvert --to script roles.ipynb
#jupyter nbconvert --to script gen_opp.ipynb


python get_min.py
#python cluster/cluster2_scrape.py

python distance/set_distance.py

#python roles.py
#python gen_opp.py