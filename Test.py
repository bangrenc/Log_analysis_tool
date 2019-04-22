# -*- coding: utf-8 -*-
__author__ = 'Byron'

import os,sys
import pandas as pd
import re
import linecache

def Model_PN_SN(FileDir):
    openFile = open(FileDir,'r',encoding='UTF-8',errors='ignore')
    model_PN_SN = []

    try:
        for Line in openFile:
            if "Marketing Name   : " in Line:
                Model = re.match(r'.*:(.*)',Line)
                if Model:
                    Model = Model.group(1)
                    model_PN_SN.append(Model)

            if "Serial Number    :" in Line:
                SN = re.match(r'.*:(.*)',Line)
                if SN:
                    SN = SN.group(1)
                    model_PN_SN.append(SN)

            if "Product Part Num :" in Line:
                PN = re.match(r'.*:(.*)', Line)
                if PN:
                    PN = PN.group(1)
                    model_PN_SN.append(PN)
                break
    except:
        print('Capture model or PN or SN error')

    openFile.close()
    return model_PN_SN

def getFileDir():
    #Get file name
    FileDir = []
    path = os.path.split(os.path.realpath(__file__))[0]
    #print path
    for file in os.listdir(path):
        file_path = os.path.join(path,file)
        if os.path.splitext(file_path)[1] =='.log':
            FileDir.append(file_path)
        else:
            pass

    return FileDir[0]


def subChunk(FileDir,model):
    subChunkData = []
    openFile = open(FileDir,'r',encoding='UTF-8',errors='ignore')

    GPU_num = 1
    if "K10" in model or "K80" in model or "M60" in model or "PH402" in model:
        GPU_num = 2
    else:
        GPU_num = 1

    i=0
    remove_nvvddOffset_2nd_value = 1
    remove_GPCOffset_2nd_value = 1
    startTest_Marked = 0
    remove_PerfPoint_2nd_value = 1
    recordErrorLineNum = 0


    for Line1 in openFile:

        subChunkTitle = 'None (Functional Test sub Chunk)'
        GPCOffset = 'None (KHz)'
        nvvddOffset = 'None (mV)'
        errorCode = 'None'
        AllerrorCode = []
        PerfPoint = 'None (PState)'
        atGPU = ''

        i = i+1

        if "Start Test Functional" in Line1 or "Start Burn-in" in Line1:
            remove_nvvddOffset_2nd_value = 1
            remove_GPCOffset_2nd_value = 1
            startTest_Marked = 1
            remove_PerfPoint_2nd_value = 1

            for subchunk_LineNum in range(10000):

                #sub chunk title
                if startTest_Marked ==1:
                    startTest_Marked = 0
                    subChunkTitle = re.match(r'.*Start(.*) timestamp',linecache.getline(FileDir,i+subchunk_LineNum))
                    if subChunkTitle:
                        subChunkTitle = subChunkTitle.group(1)
                    # print(subChunkTitle)

                # GPCClk Offset
                if remove_GPCOffset_2nd_value == 1:
                    if "Setting GPC frequency" in linecache.getline(FileDir,i+subchunk_LineNum):
                        remove_GPCOffset_2nd_value = 0
                        GPCOffset = re.match(r'.*Setting GPC frequency for PState.\d to \d* \S* \S* \S (.*) offset',linecache.getline(FileDir,i+subchunk_LineNum))
                        if GPCOffset:
                            GPCOffset = GPCOffset.group(1)
                            #print(GPCOffset)

                    elif "Setting frequency offset for" in linecache.getline(FileDir,i+subchunk_LineNum):
                        remove_GPCOffset_2nd_value = 0
                        GPCOffset = re.match(r'.*Setting frequency offset for PState \d to (.*)',linecache.getline(FileDir,i+subchunk_LineNum))
                        if GPCOffset:
                            GPCOffset = GPCOffset.group(1)
                            #print(GPCOffset)

                #nvvdd offset
                if remove_nvvddOffset_2nd_value == 1:
                    if "Setting nvvdd voltage" in linecache.getline(FileDir,i+subchunk_LineNum):
                        remove_nvvddOffset_2nd_value = 0
                        nvvddOffset = re.match(r'.*voltage offset to(.*)',linecache.getline(FileDir,i+subchunk_LineNum))
                        if nvvddOffset:
                            nvvddOffset = nvvddOffset.group(1)
                        # print(nvvddOffset)

                #Perf Point
                if remove_PerfPoint_2nd_value == 1:
                    if "Switched to PState" in linecache.getline(FileDir,i+subchunk_LineNum):
                        remove_PerfPoint_2nd_value = 0
                        PerfPoint = re.match(r'.*Switched to (.*). Pcie',linecache.getline(FileDir,i+subchunk_LineNum))
                        if PerfPoint:
                            PerfPoint = PerfPoint.group(1)
                            # print(PerfPoint)

                #Error code
                if "ERROR: " in linecache.getline(FileDir,i+subchunk_LineNum) or "CRC check failed" in linecache.getline(FileDir,i+subchunk_LineNum)\
                        or "New total EDC errors" in linecache.getline(FileDir,i+subchunk_LineNum) or "Error 0" in linecache.getline(FileDir,i+subchunk_LineNum):
                    for j in range(50):
                       if "Exit 000000000000" in linecache.getline(FileDir,i+subchunk_LineNum+j):
                           break

                       if "Exit " in linecache.getline(FileDir,i+subchunk_LineNum+j):
                           if recordErrorLineNum == i+subchunk_LineNum+j:
                               pass
                           else:
                               errorCode = re.match(r'.*Exit (\d.*):',linecache.getline(FileDir,i+subchunk_LineNum+j))
                               if errorCode:
                                   errorCode = errorCode.group(1)
                                   recordErrorLineNum = i + subchunk_LineNum + j
                                   AllerrorCode.append(errorCode)

                                   #Check if error at which GPU
                                   if GPU_num == 2:
                                       for k in range(100000):
                                           if "Failure(s) :" in linecache.getline(FileDir,i+subchunk_LineNum+j+k):
                                               for m in range(30):
                                                   if "Error Code on GPU" in linecache.getline(FileDir,i+subchunk_LineNum+j+k+m):
                                                       break
                                                   if errorCode in linecache.getline(FileDir,i+subchunk_LineNum+j+k+m):
                                                       atGPU = re.match(r'.*(\(.*\))',linecache.getline(FileDir,i+subchunk_LineNum+j+k+m))
                                                       if atGPU:
                                                           atGPU = atGPU.group(1)
                                                           AllerrorCode.append('at GPU ' + atGPU)

                                           if "Error Code on GPU" in linecache.getline(FileDir,i+subchunk_LineNum+j+k):
                                               break

                       elif "Error 0" in linecache.getline(FileDir, i + subchunk_LineNum + j):
                           for n in range(5):
                               if "Exit 000000000000" in linecache.getline(FileDir,i+subchunk_LineNum+j-n):
                                   break
                               if "Exit " in linecache.getline(FileDir,i+subchunk_LineNum+j-n):
                                   if recordErrorLineNum == i+subchunk_LineNum+j-n:
                                       pass
                                   else:
                                       errorCode = re.match(r'.*Exit (\d.*):',linecache.getline(FileDir,i+subchunk_LineNum+j-n))
                                       recordErrorLineNum = i + subchunk_LineNum + j - n
                                       if errorCode:
                                           errorCode = errorCode.group(1)
                                           AllerrorCode.append(errorCode)

                                           #Check if error at which GPU
                                           if GPU_num == 2:
                                               for k in range(100000):
                                                   if "Failure(s) :" in linecache.getline(FileDir,i+subchunk_LineNum+j+k):
                                                       for m in range(30):
                                                           if "Error Code on GPU" in linecache.getline(FileDir,i+subchunk_LineNum+j+k+m):
                                                               break
                                                           if errorCode in linecache.getline(FileDir,i+subchunk_LineNum+j+k+m):
                                                               atGPU = re.match(r'.*(\(.*\))',linecache.getline(FileDir,i+subchunk_LineNum+j+k+m))
                                                               if atGPU:
                                                                   atGPU = atGPU.group(1)
                                                                   AllerrorCode.append('at GPU '+atGPU)
                                                                   #print(atGPU)

                                                   if "Error Code on GPU" in linecache.getline(FileDir,i+subchunk_LineNum+j+k):
                                                       break
                               if "Enter " in linecache.getline(FileDir,i+subchunk_LineNum+j-n):
                                   break


                       if "Enter " in linecache.getline(FileDir,i+subchunk_LineNum+j):
                            break
                       elif "Exit 000000000000" in linecache.getline(FileDir,i+subchunk_LineNum+j):
                           break
                       elif "Error Code" in linecache.getline(FileDir,i+subchunk_LineNum+j):
                           break
                       elif "GPU tests completed" in linecache.getline(FileDir,i+subchunk_LineNum+j):
                           break

                if "Start Test Functional" in linecache.getline(FileDir,i+subchunk_LineNum+1) or "Start Burn-in" in linecache.getline(FileDir,i+subchunk_LineNum+1):
                    if GPCOffset == "None (KHz)" and nvvddOffset =="None (mV)" and PerfPoint == "None (PState)":
                        pass
                    else:
                        subChunkData.append(subChunkTitle)
                        subChunkData.append(GPCOffset)
                        subChunkData.append(nvvddOffset)
                        subChunkData.append(AllerrorCode)
                        subChunkData.append(PerfPoint)
                        #subChunkData.append(atGPU)
                    break

                elif "Error Code" in linecache.getline(FileDir, i+subchunk_LineNum+1):
                    subChunkData.append(subChunkTitle+"\n")
                    subChunkData.append(GPCOffset)
                    subChunkData.append(nvvddOffset)
                    subChunkData.append(AllerrorCode)
                    subChunkData.append(PerfPoint)
                    #subChunkData.append(atGPU)
                    break

                elif subchunk_LineNum == 9999:
                    subChunkData.append(subChunkTitle)
                    subChunkData.append(GPCOffset)
                    subChunkData.append(nvvddOffset)
                    subChunkData.append(AllerrorCode)
                    subChunkData.append(PerfPoint)
                    #subChunkData.append(atGPU)
                    break

    openFile.close()
    return subChunkData

def main():
    FileDir = getFileDir()
    model_PN_SN = Model_PN_SN(FileDir)

    model = model_PN_SN[0]
    SN = model_PN_SN[1]
    PN = model_PN_SN[2]

    subChunkData = subChunk(FileDir,model)

    modelList = []
    SNList = []
    PNList = []

    subChunkTitle = []
    GPCClkOffset = []
    nvvddOffset = []
    errorCode = []
    PerfP = []
    #atGPU = []

    for i in range(len(subChunkData)):
        if "Test" in subChunkData[i]:
            subChunkTitle.append(subChunkData[i])
        elif "KHz" in subChunkData[i]:
            GPCClkOffset.append(subChunkData[i])
        elif "mV" in subChunkData[i]:
            nvvddOffset.append(subChunkData[i])
        elif "PState" in subChunkData[i]:
            PerfP.append(subChunkData[i])
        # elif "GPU" in subChunkData[i]:
        #     atGPU.append(subChunkData[i])
        else:
            errorCode.append(subChunkData[i])

    for i in range(len(subChunkTitle)):
        if model != '':
            modelList.append(model)
            model = ''
        else:
            modelList.append(model)

        if PN != '':
            PNList.append(PN)
            PN = ''
        else:
            PNList.append(PN)

        if SN != '':
            SNList.append("'"+SN)
            SN = ''
        else:
            SNList.append(SN)

    result = pd.DataFrame(columns=['model','PN','SN','Sub Chunk','PerfPoint','GPCClk Offset','NVVDD Offset','Error Code'])

    result['model'] = modelList
    result['PN'] = PNList
    result['SN'] = SNList
    result['Sub Chunk'] = subChunkTitle
    result['PerfPoint'] = PerfP
    result['GPCClk Offset'] = GPCClkOffset
    result['NVVDD Offset'] = nvvddOffset
    result['Error Code'] = errorCode
    #result['GPU'] = atGPU

    result.to_csv('Result.csv',index=False)

if __name__ == '__main__':
    main()










