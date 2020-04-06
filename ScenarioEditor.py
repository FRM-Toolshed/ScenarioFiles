#!/usr/bin/env python

import os
import csv
import re
import collections
import pandas as pd
import numpy as np
from decimal import *

################################################################# HelperFunctions ####################################################################
def equityalloc(vixValue):
    return min(max(100*0.11/vixValue,0.25), 1)

def bondalloc(vixValue):
    return min(1 -min(max(100*0.11/vixValue,0.25), 1), 0.44)

def calcVCF(equityalloc, bondalloc, equityRate, bondRate):
    return equityalloc*equityRate + bondalloc*bondRate

def default1(Timestep, equityreturn) -> float:
    if Timestep == 0:
        return 0
    else:
        return np.log(1 + float(equityreturn))

def default10yrT(Timestep, treturn, defaultvalue):
    if Timestep == 0:
        return defaultvalue
    else:
        return treturn + 0.000244

def default1yrT(Timestep, treturn, defaultvalue):
    if Timestep == 0:
        return defaultvalue
    else:
        return treturn + 0.001967

def default2(Timestep, treturn, defaultvalue):
    if Timestep == 0:
        return defaultvalue
    else:
        return treturn

def resplit(xval):
    return int(re.split('_', xval)[3])

################################################################# CLEAN  VCF ####################################################################

def truncateVCF(ScenarioFile, directory, outfile):
    os.chdir(directory)

    colToNum = {}

    # listofOther = ['No','Run Id','ScnName','Row']
    listofOther = ['ScnName']

    listofEquity = ['EQ-US-VALIC-Growth rate', 'EQ-ITGVT-VALIC-Growth rate', 'EQ-LTCORP-VALIC-Growth rate', 'EQ-AGGR-VALIC-Growth rate', 'EQ-SMALL-VALIC-Growth rate','EQ-INTL-VALIC-Growth rate',
    'EQ-MONEY-VALIC-Growth rate','EQ-BALANCED-VALIC-Growth rate','EQ-FIXED-VALIC-Growth rate']

    listofRates = ['IR-TRSY-USD-3 month bills',	'IR-TRSY-USD-6 month bills','IR-TRSY-USD-12 month bills','IR-TRSY-USD-2 year bonds',	
    'IR-TRSY-USD-3 year bonds',	'IR-TRSY-USD-5 year bonds',	'IR-TRSY-USD-7 year bonds',	'IR-TRSY-USD-10 year bonds','IR-TRSY-USD-20 year bonds','IR-TRSY-USD-30 year bonds']
    
    vix = ["VO-VIX-User value"]

    listComb = listofOther # + listofRates + listofEquity + vix

    f1 = open(ScenarioFile, 'r+')
    f2 = open(outfile, 'w+')

    l = f1.readlines()

    header = True

    for line in l:
        if header:
            splitline = re.split('\|', line)
            for x, y in enumerate(splitline):
                if y in listComb:
                    colToNum[y] = x

            header = False
            headerOut = ','.join(listComb) + '\n'
            f2.write(headerOut)

        else:
            splitline = re.split('\|', line)
            lineout = []

            for item in listComb:
                lineout.append(splitline[colToNum[item]])
            
            lineoutStr = ','.join(lineout) + '\n'
            f2.write(lineoutStr)
    
    f1.close()
    f2.close()


def cleanVCF(VCFScenarioFile, directory, outfile):
    os.chdir(directory)
    colnames = list(range(0, 601))

    data = pd.read_csv(VCFScenarioFile, header = None)
    # datascen = pd.read_csv(ScenarioFile)

    data["ScenNum"] = data[data.columns[0]].apply(resplit)
    data.sort_values(by = ['ScenNum'])

    data = data.drop(data.columns[0], axis=1)
    data = data.drop(["ScenNum"], axis = 1)
    
    datanew = data.to_numpy().flatten()    
    
    datanew.to_csv(outfile, index = False)



################################################################# CLEAN  ScenFile ####################################################################

def clean(ScenarioFile, directory, outfile):
    os.chdir(directory)

    listofEquity = ['EQ-US-VALIC-Growth rate', 'EQ-ITGVT-VALIC-Growth rate', 'EQ-LTCORP-VALIC-Growth rate', 'EQ-AGGR-VALIC-Growth rate', 'EQ-SMALL-VALIC-Growth rate','EQ-INTL-VALIC-Growth rate',
    'EQ-MONEY-VALIC-Growth rate','EQ-BALANCED-VALIC-Growth rate','EQ-FIXED-VALIC-Growth rate']

    listofRates = ['IR-TRSY-USD-3 month bills',	'IR-TRSY-USD-6 month bills','IR-TRSY-USD-12 month bills','IR-TRSY-USD-2 year bonds',	
    'IR-TRSY-USD-3 year bonds',	'IR-TRSY-USD-5 year bonds',	'IR-TRSY-USD-7 year bonds',	'IR-TRSY-USD-10 year bonds','IR-TRSY-USD-20 year bonds','IR-TRSY-USD-30 year bonds']
    
    
    data = pd.read_csv(ScenarioFile)
    data = data[data['ScnName'].str.contains("VM21_AAA")]
    
    #### Convert to monthly continuous ######

    datanew = pd.DataFrame(columns=[])
    datanew["Scenario"] = data["ScnName"].apply(lambda x: int(re.split("_", x)[3]))
    datanew["Timestep"] = data["Row"].apply(lambda x: int(x.replace("M","")))
    for equitycol in listofEquity:
        datanew[equitycol.replace(" rate","")] = data[equitycol].apply(lambda x: pow((1 + x/100),(1/12))-1)

    datanew["VIX_"] = data["VO-VIX-User value"]

    datanew["Equity"] = data["VO-VIX-User value"].apply(equityalloc)
    datanew["Bond"] = data["VO-VIX-User value"].apply(bondalloc)
    datanew["VCF_"] = np.vectorize(calcVCF)(datanew["Equity"],datanew["Bond"], datanew['EQ-US-VALIC-Growth'], datanew['EQ-FIXED-VALIC-Growth'])

    for ratesCol in listofRates:
        datanew[ratesCol] = data[ratesCol]/100

    datanew = datanew[datanew['Timestep'] <= 600]
    datanew_new = datanew.sort_values(by = ['Scenario', 'Timestep'])

    datanew_new.to_csv(outfile, index = False)


def cleanwVCF(ScenarioFile, VCFFile, directory, outfile):
    os.chdir(directory)

    listofEquity = ['EQ-US-VALIC-Growth rate', 'EQ-ITGVT-VALIC-Growth rate', 'EQ-LTCORP-VALIC-Growth rate', 'EQ-AGGR-VALIC-Growth rate', 'EQ-SMALL-VALIC-Growth rate','EQ-INTL-VALIC-Growth rate',
    'EQ-MONEY-VALIC-Growth rate','EQ-BALANCED-VALIC-Growth rate','EQ-FIXED-VALIC-Growth rate']

    listofRates = ['IR-TRSY-USD-3 month bills',	'IR-TRSY-USD-6 month bills','IR-TRSY-USD-12 month bills','IR-TRSY-USD-2 year bonds',	
    'IR-TRSY-USD-3 year bonds',	'IR-TRSY-USD-5 year bonds',	'IR-TRSY-USD-7 year bonds',	'IR-TRSY-USD-10 year bonds','IR-TRSY-USD-20 year bonds','IR-TRSY-USD-30 year bonds']
    
    data = pd.read_csv(ScenarioFile)
    
    dataVCF = pd.read_csv(VCFFile)

    dataVCF["VCF_"] = dataVCF["VCF"].apply(lambda x: pow((1 + x/100),(1/12))-1)

    #### Convert to monthly continuous ######

    datanew = pd.DataFrame(columns=[])
    datanew["Scenario"] = data["ScnName"].apply(lambda x: int(re.split("_", x)[3]))
    datanew["Timestep"] = data["Row"].apply(lambda x: int(x.replace("M","")))

    for equitycol in listofEquity:
        datanew[equitycol.replace(" rate","")] = data[equitycol].apply(lambda x: pow((1 + x/100),(1/12))-1)

    datanew["VIX_"] = data["VO-VIX-User value"]

    # datanew["Equity"] = data["VO-VIX-User value"].apply(equityalloc)
    # datanew["Bond"] = data["VO-VIX-User value"].apply(bondalloc)
    # datanew["VCF_"] = np.vectorize(calcVCF)(datanew["Equity"],datanew["Bond"], datanew['EQ-US-VALIC-Growth'], datanew['EQ-FIXED-VALIC-Growth'])

    for ratesCol in listofRates:
        datanew[ratesCol] = data[ratesCol]/100

    ##### Join VCF ####
    dataJoined = pd.merge(datanew, dataVCF, how='left', left_on =['Scenario', 'Timestep'], right_on = ['ScenNumVCF', 'TimestepVCF'])
    dataJoined_new = dataJoined.sort_values(by = ['Scenario', 'Timestep'])

    dataJoined_new.to_csv(outfile, index = False)

################################################################# Join Company ####################################################################

def joinCompany(ScenarioFileClean, CompanyScenarioFile, directory, outfile):
    os.chdir(directory)
    data = pd.read_csv(ScenarioFileClean)
    dataCompany = pd.read_csv(CompanyScenarioFile)

    finalCols = dataCompany.columns

    colsFrom = {'US':'EQ-US-VALIC-Growth',
     'INTGOV': 'EQ-ITGVT-VALIC-Growth',
     'LTCORP': 'EQ-LTCORP-VALIC-Growth',
     'FIXED':'EQ-FIXED-VALIC-Growth',
     'VCF': 'VCF_',
     'MONEY': 'EQ-MONEY-VALIC-Growth',
     'SMALL': 'EQ-SMALL-VALIC-Growth',
     'INT': 'EQ-INTL-VALIC-Growth',
     'AGG': 'EQ-AGGR-VALIC-Growth',
     'BALANCED': 'EQ-BALANCED-VALIC-Growth'}


    DefaultVals = {
        'VIX': 13.78,
        'YEARTHRITYRATE': 0.0239,
        'YEARONESWAP': 0.017704,
        'YEARTENSWAP': 0.01895,
        'Fund10YR': 0.01919
    }

    DefaultCols = {
        'VIX': 'VIX_',
        'YEARTHRITYRATE': 'IR-TRSY-USD-30 year bonds',
        'Fund10YR': 'IR-TRSY-USD-10 year bonds'
    }

    dataJoined = pd.merge(dataCompany, data, how='left', left_on =['ScenNum', 'TimeStep'], right_on = ['Scenario', 'Timestep'])
    
    datanew = pd.DataFrame(columns=[])

    for colname in finalCols:
        if colname in colsFrom.keys():
            datanew[colname] = np.vectorize(default1, otypes = [np.float])(dataJoined['TimeStep'], dataJoined[colsFrom[colname]])
            # datanew[colname] = datanew[colname].apply(lambda x: Decimal(x).normalize())
        elif colname in DefaultVals.keys():
            if colname == 'YEARTENSWAP':
                datanew[colname] = np.vectorize(default10yrT, otypes = [np.float])(dataJoined['TimeStep'], dataJoined['IR-TRSY-USD-10 year bonds'], DefaultVals[colname])
                # datanew[colname] = datanew[colname].apply(lambda x: Decimal(x).normalize())
            elif colname == 'YEARONESWAP':
                datanew[colname] = np.vectorize(default1yrT, otypes = [np.float])(dataJoined['TimeStep'], dataJoined['IR-TRSY-USD-10 year bonds'], DefaultVals[colname])
                # datanew[colname] = datanew[colname].apply(lambda x: Decimal(x).normalize())
            else:
                datanew[colname] = np.vectorize(default2, otypes = [np.float])(dataJoined['TimeStep'], dataJoined[DefaultCols[colname]], DefaultVals[colname])
                # datanew[colname] = datanew[colname].apply(lambda x: Decimal(x).normalize())
        else:
            datanew[colname] = dataCompany[colname]
            # if 'int' in str(type(dataCompany[colname][0])):
            #     datanew[colname] = dataCompany[colname]
            # else:
            #     datanew[colname] = dataCompany[colname].apply(lambda x: Decimal(x).normalize())

    datanew.to_csv(outfile, index = False)


def joinForwards(ScenarioFileClean, Forwards, directory, outfile):
    os.chdir(directory)
    data = pd.read_csv(ScenarioFileClean)
    dataForwards = pd.read_csv(Forwards)

    finalCols = data.columns

    ForwardColumns = {'USD FWDRATE 1y':'USD FWDRATE 1y_','USD FWDRATE 2y':'USD FWDRATE 2y_',
        	'USD FWDRATE 3y':'USD FWDRATE 3y_','USD FWDRATE 4y':'USD FWDRATE 4y_','USD FWDRATE 5y':'USD FWDRATE 5y_',
            'USD FWDRATE 6y':'USD FWDRATE 6y_',	'USD FWDRATE 7y':'USD FWDRATE 7y_',	'USD FWDRATE 8y':'USD FWDRATE 8y_',
        	'USD FWDRATE 9y':'USD FWDRATE 9y_',	'USD FWDRATE 10y':'USD FWDRATE 10y_',	'USD FWDRATE 11y':'USD FWDRATE 11y_',
            'USD FWDRATE 12y':'USD FWDRATE 12y_',	'USD FWDRATE 13y':'USD FWDRATE 13y_',	'USD FWDRATE 14y':'USD FWDRATE 14y_',
            'USD FWDRATE 15y':'USD FWDRATE 15y_',	'USD FWDRATE 16y':'USD FWDRATE 16y_',	'USD FWDRATE 17y':'USD FWDRATE 17y_',
            'USD FWDRATE 18y':'USD FWDRATE 18y_',	'USD FWDRATE 19y':'USD FWDRATE 19y_',	'USD FWDRATE 20y':'USD FWDRATE 20y_',
            'USD FWDRATE 21y':'USD FWDRATE 21y_',	'USD FWDRATE 22y':'USD FWDRATE 22y_',	'USD FWDRATE 23y':'USD FWDRATE 23y_',
            'USD FWDRATE 24y':'USD FWDRATE 24y_',	'USD FWDRATE 25y':'USD FWDRATE 25y_',	'USD FWDRATE 26y':'USD FWDRATE 26y_',
            'USD FWDRATE 27y':'USD FWDRATE 27y_',	'USD FWDRATE 28y':'USD FWDRATE 28y_',	'USD FWDRATE 29y':'USD FWDRATE 29y_',
            'USD FWDRATE 30y':'USD FWDRATE 30y_'
}

    DefaultVals = {  'USD FWDRATE 1y':0.0176885477060511,'USD FWDRATE 2y':0.0160480921412171,'USD FWDRATE 3y':0.0166944939562567,'USD FWDRATE 4y':0.017645992792445,'USD FWDRATE 5y':0.0180649035852169,
    'USD FWDRATE 6y':0.0193239037900342,'USD FWDRATE 7y':0.0200354604874232,'USD FWDRATE 8y':0.0206458011996901,'USD FWDRATE 9y':0.0213479354795383,'USD FWDRATE 10y':0.022060232552314,
    'USD FWDRATE 11y':0.0198642922109526,'USD FWDRATE 12y':0.0200499679499767,'USD FWDRATE 13y':0.0202379197456715,'USD FWDRATE 14y':0.0204282364922842,'USD FWDRATE 15y':0.0206210111269701,
    'USD FWDRATE 16y':0.0208163408651261,'USD FWDRATE 17y':0.0210143274521451,'USD FWDRATE 18y':0.0212150774328757,'USD FWDRATE 19y':0.0214187024403385,'USD FWDRATE 20y':0.0216253195052878,
    'USD FWDRATE 21y':0.0225682339372708,'USD FWDRATE 22y':0.0228559454648273,'USD FWDRATE 23y':0.0231486073525285,'USD FWDRATE 24y':0.0234464582703565,'USD FWDRATE 25y':0.023749750823161,
    'USD FWDRATE 26y':0.0240587525943581,'USD FWDRATE 27y':0.0243737472844084,'USD FWDRATE 28y':0.02469503595355,'USD FWDRATE 29y':0.0250229383805693,'USD FWDRATE 30y':0.025357794550109 
}

    dataJoined = pd.merge(data, dataForwards, how='left', left_on =['ScenNum', 'TimeStep'], right_on = ['Scenario', 'Timestep'])
    
    datanew = pd.DataFrame(columns=[])

    for colname in finalCols:
        if colname in ForwardColumns:
            datanew[colname] = np.vectorize(default2, otypes = [np.float])(dataJoined['TimeStep'], dataJoined[ForwardColumns[colname]], DefaultVals[colname])
        else:
            datanew[colname] = data[colname]
        
    
    datanew.to_csv(outfile, index = False)






if __name__ == "__main__":
    ####### Trims VCF File down to select columns ######
    # truncateVCF('ParallelRunScen.txt', r'C:\Users\bailey.lin\Documents', '2019Q4_VSU_Scndata_namesOnly.csv') 
    
    ####### Sorts VCF File by Scenario Number #########
    # cleanVCF('VM21_Scn_VCF_20183112.csv', r'C:\Users\bailey.lin\Documents', '_VCF_Clean.csv') 
    
    ####### Trims Scenario File down to select columns, converts Monthly Discrete Equity Returns to Continuous  #########
    # clean('2019Q4_VSU_Scndata.csv', r'C:\Users\bailey.lin\Documents', '2019Q4_VSU_Scndata_Clean.csv')
    
    ####### Join 2 Scenario Files  #########
    # joinCompany('2019Q4_VSU_Scndata_Clean.csv', 'RWScenario_monthly_50yr.txt', r'C:\Users\bailey.lin\Documents', 'RWScenario_monthly_50yr_2019YE.csv' )
    
    ####### Same as Clean, but also joins Scenario File with VCF File #########
    # cleanwVCF('2018Q4_VSU_Scndata.csv', '_VCF_Clean.csv', r'C:\Users\bailey.lin\Documents', '2018Q4_VSU_Scndata_Clean_wVCF2.csv')
    
    ####### Join Scenario File with Forwards File ################
    joinForwards('RWScenario_monthly_50yr_20191231.csv', 'Forwards_2019YE.csv', r'C:\Users\bailey.lin\Documents', 'RWScenario_monthly_50yr_20191231_wForwards.csv')