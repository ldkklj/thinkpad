import pandas as pd


dd = [{'time': 1, 'price': 11},{'time': 2, 'price': 22}]
#cc={"time":dd['time'],"price":dd['price']}

def poly(singlePairerecords):
    df = pd.DataFrame(dd)
    print(df)

poly(dd)

