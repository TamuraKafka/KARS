import math,csv,random
import time

import numpy as np
import sys

class CRH:
    def __init__(self,e2wl,w2el,label_set,datatype,distancetype):
        self.e2wl = e2wl
        self.w2el = w2el
        self.weight = dict()
        self.label_set = label_set
        self.datatype = datatype
        self.distype = distancetype


    def distance_calculation(self,example,label):

        if self.datatype == 'continuous' and self.distype == 'normalized absolute loss':
            if self.truth[example] != float(label) and self.std[example]==0:
                print('error1 !!!!!')
            if self.truth[example] == float(label):
                return 0.0
            else:
                return math.fabs(self.truth[example] - float(label))/self.std[example]

        elif self.datatype == 'continuous' and self.distype == 'normalized square loss':
            if self.truth[example] != float(label) and self.std[example]==0:
                # print(self.truth)
                # print(self.truth[example])
                # print(label)
                # print(float(label))
                print('error2 !!!!!')
            if self.truth[example] == float(label):
                return 0.0
            else:
                return ((self.truth[example] - float(label))**2)/self.std[example]

        elif self.datatype == 'categorical' and self.distype == '0/1 loss':
            if self.truth[example] != label:
                return 1.0
            else:
                return 0.0
        else:
            print('datatype or distancetype error!')

    def examples_truth_calculation(self):
        self.truth = dict()

        if self.datatype == 'continuous' and self.distype == 'normalized absolute loss':

            for example, worker_label_set in self.e2wl.items():
                # print(self.truth)
                temp = dict()
                sum_weight = 0.0
                for worker, label in worker_label_set:
                    if label in temp:
                        temp[float(label)] = temp[float(label)] + self.weight[worker]
                    else:
                        temp[float(label)] = self.weight[worker]
                    sum_weight = sum_weight + self.weight[worker]

                temp = temp.items()
                temp = sorted(temp, key=lambda X : X[0])

                median_weight = 0.0
                for i in range(len(temp)):
                    median_weight = median_weight + temp[i][1]
                    if (median_weight >= 0.5*sum_weight):
                        self.truth[example] = temp[i][0]
                        break

        elif self.datatype == 'continuous' and self.distype == 'normalized square loss':

            for example, worker_label_set in self.e2wl.items():
                temp = 0.0
                sum_weight = 0.0
                for worker, label in worker_label_set:
                    temp = temp + self.weight[worker] * float(label)
                    sum_weight = sum_weight + self.weight[worker]

                self.truth[example] = temp / sum_weight


        elif self.datatype == 'categorical' and self.distype == '0/1 loss':
            for example, worker_label_set in self.e2wl.items():
                temp = dict()
                for worker, label in worker_label_set:
                    if label in temp:
                        temp[label] = temp[label] + self.weight[worker]
                    else:
                        temp[label] = self.weight[worker]

                max = 0
                for label, num in temp.items():
                    if num > max:
                        max = num

                candidate = []
                for label, num in temp.items():
                    if max == num:
                        candidate.append(label)

                if len(candidate)>0:
                    self.truth[example] = random.choice(candidate)
                else:
                    self.truth[example] = random.choice(label_set)

        else:
            print('datatype or distancetype error!')

    def workers_weight_calculation(self):
        #weight_sum = 0.0
        weight_max = 0.0

        self.weight = dict()

        for worker, example_label_set in self.w2el.items():
            dif = 0.0
            for example, label in example_label_set:
                dif = dif + self.distance_calculation(example,label)

            if dif==0.0 or math.isnan(dif):
                #print worker, dif
                # print(dif)
                dif = 0.00000001

            self.weight[worker] = dif

            #weight_sum = weight_sum + self.weight[worker]
            if self.weight[worker] > weight_max:
                weight_max = self.weight[worker]

        for worker in self.w2el.keys():
            #self.weight[worker] = self.weight[worker] / weight_sum
            self.weight[worker] = self.weight[worker] / weight_max

        for worker in self.w2el.keys():
            self.weight[worker] = - math.log(self.weight[worker] + 0.0000001 ) + 0.0000001


    def Init_truth(self):
        self.truth = dict()
        self.std = dict()

        if self.datatype == 'continuous':
            for example, worker_label_set in self.e2wl.items():
                temp = []
                for _, label in worker_label_set:
                    temp.append(float(label))

                self.truth[example] = np.median(temp)  # using median as intial value
                #self.truth[example] = np.mean(temp)  # using mean as initial value
                self.std[example] = np.std(temp)


        else:
            # using majority voting to obtain initial value
            for example, worker_label_set in self.e2wl.items():
                temp = dict()
                for _, label in worker_label_set:
                    if label in temp:
                        temp[label] = temp[label] + 1
                    else:
                        temp[label] = 1

                max = 0
                for label, num in temp.items():
                    if num > max:
                        max = num

                candidate = []
                for label, num in temp.items():
                    if max == num:
                        candidate.append(label)

                self.truth[example] = random.choice(candidate)


    def get_e2lpd(self):

        if self.datatype == 'continuous':
            return self.truth
        else:
            e2lpd = dict()
            for example, worker_label_set in self.e2wl.items():
                temp = dict()
                sum = 0.0
                for worker, label in worker_label_set:
                    if label in temp:
                        temp[label] = temp[label] + self.weight[worker]
                    else:
                        temp[label] = self.weight[worker]
                    sum = sum + self.weight[worker]

                for label in temp.keys():
                    temp[label] = temp[label] / sum

                e2lpd[example] = temp

            return e2lpd

    def get_workerquality(self):
        sum_worker = sum(self.weight.values())
        norm_worker_weight = dict()
        for worker in self.weight.keys():
            norm_worker_weight[worker] = self.weight[worker] / sum_worker
        return norm_worker_weight

    def Run(self,iterr):

        self.Init_truth()
        while iterr > 0:
            #print getaccuracy(sys.argv[2], self.truth, datatype)
            self.workers_weight_calculation()
            # print(self.truth)
            self.examples_truth_calculation()

            iterr -= 1

        return self.get_e2lpd(), self.get_workerquality()



###################################
# The above is the EM method (a class)
# The following are several external functions
###################################

# def getaccuracy(truthfile, predict_truth, datatype):
#     e2truth = {}
#     f = open(truthfile, 'r')
#     reader = csv.reader(f)
#     next(reader)

#     for line in reader:
#         example, truth = line
#         e2truth[example] = truth

#     tcount = 0.0
#     count = 0

#     for e, ptruth in predict_truth.items():

#         if e not in e2truth:
#             continue

#         count += 1

#         if datatype=='continuous':
#             tcount = tcount + (ptruth-float(e2truth[e]))**2 #root of mean squared error
#             #tcount = tcount + math.fabs(ptruth-float(e2truth[e])) #mean of absolute error
#         else:
#             if ptruth == e2truth[e]:
#                 tcount += 1

#     if datatype=='continuous':
#         return pow(tcount/count,0.5)  #root of mean squared error
#         #return tcount/count  #mean of absolute error
#     else:
#         return tcount*1.0/count

def getaccuracy(truthfile, predict_truth, datatype):
    e2truth = {}
    f = open(truthfile, 'r')
    reader = csv.reader(f)
    next(reader)

    for line in reader:
        example, truth = line
        e2truth[example] = truth

    tcount1 = 0
    tcount2 = 0
    count = 0

    for e, ptruth in predict_truth.items():

        if e not in e2truth:
            continue

        count += 1

        if datatype == 'continuous':
            tcount1 = tcount1 + (ptruth - float(e2truth[e])) ** 2  # root of mean squared error
            tcount2 = tcount2 + math.fabs(ptruth - float(e2truth[e]))  # mean of absolute error
        else:
            if ptruth == e2truth[e]:
                tcount1 += 1

    if datatype == 'continuous':
        return tcount2 / count, pow(tcount1 / count, 0.5)  # root of mean squared error
        # return tcount/count  #mean of absolute error
    else:
        return tcount1 * 1.0 / count


def gete2wlandw2el(datafile):
    e2wl = {}
    w2el = {}
    label_set=[]

    f = open(datafile, 'r')
    reader = csv.reader(f)
    next(reader)

    for line in reader:
        worker, example, label = line

        if example not in e2wl:
            e2wl[example] = []
        e2wl[example].append([worker,label])

        if worker not in w2el:
            w2el[worker] = []
        w2el[worker].append([example, label])

        if label not in label_set:
            label_set.append(label)

    return e2wl,w2el,label_set



# if __name__ == "__main__":
def PM_CRH_Output(datafile,truthfile):
    startTime = time.time()
    # if len(sys.argv)>=4 and sys.argv[3] == 'continuous':
    #     datatype = r'continuous'
    #     distancetype = r'normalized absolute loss'
    #     #distancetype= r'normalized square loss'
    # else:
    #     datatype = r'categorical'
    #     distancetype = r'0/1 loss'


    # datatype = sys.argv[2]
    datatype = r'continuous'
    if datatype == r'continuous':
        distancetype = r'normalized square loss'
    else:
        distancetype = r'0/1 loss'

    # datafile = sys.argv[1]


    # datafile = '../datasets/QuantitativeCrowdsourcing/DouBanDatasets/Douban_201t_26818w/Y.csv'
    # truthfile = '../datasets/QuantitativeCrowdsourcing/DouBanDatasets/Douban_201t_26818w/truth.csv'

    # datafile = '../datasets/QuantitativeCrowdsourcing/GoodReadsDatasets/GoodReads_309t_122934w/Y.csv'
    # truthfile = '../datasets/QuantitativeCrowdsourcing/GoodReadsDatasets/GoodReads_309t_122934w/truth.csv'


    e2wl,w2el,label_set = gete2wlandw2el(datafile)
    crh = CRH(e2wl,w2el,label_set,datatype,distancetype)
    e2lpd, weight = crh.Run(10)

    mse, rmse = getaccuracy(truthfile, crh.truth, datatype)
    # print("PM-CRH---MAE:", mse)
    # print("PM-CRH---RMSE:", rmse)

    endTime = time.time()
    runtime = int(endTime - startTime)
    return rmse , mse , runtime