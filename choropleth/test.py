import functions

name = 'india'

m = functions.createMap(name)

df_data = functions.pd.read_csv('test.csv')

functions.staticPlot(m, name, df_data)

functions.plt.show()