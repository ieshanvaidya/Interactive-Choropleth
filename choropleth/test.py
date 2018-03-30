import functions

name = 'india'

m = functions.createMap(name)

df_data = functions.pd.read_csv('test2.csv')

#functions.staticPlot(m, name, df_data)

#functions.plt.show()

functions.interactivePlot(name, df_data)