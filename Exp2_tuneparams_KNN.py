from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import recall_score
from sklearn.metrics import classification_report
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
# from __future__ import print_function, division
from sklearn.svm import SVC
from matplotlib import pyplot as plt
from PIL import Image
import numpy as np
import glob
import skimage.io as io
import time
import seaborn as sns
import os


# Load images

pairs = [('Birdo', 'Yoshi'), 
		('Bowser', 'MiniBowser'),
		('Mario', 'Luigi'), 
		('Peach', 'Rosalina')]
ch_map ={('Birdo', 'Yoshi'): 		{ 'Birdo': 0, 'Yoshi': 1}, 
		('Bowser', 'MiniBowser'): 	{ 'Bowser': 0, 'MiniBowser': 1},
		('Mario', 'Luigi'): 		{ 'Mario': 0, 'Luigi': 1},
		('Peach', 'Rosalina'): 		{ 'Peach': 0, 'Rosalina': 1}}

imgs = {} 
labels = {}
data = {} 

print('Loading data ... ')
for i, pair in enumerate(pairs):
	imgs[pair] = {} 
	labels[pair] = {}

	for folder in ['train', 'val']:
		imgs[pair][folder] = [] 
		labels[pair][folder] = []
		for ch in pair:
			path = '../data/images/CNN-1'
			dirr = os.path.join(path, folder ,ch, '*.jpg')
			for im_path in glob.glob(dirr):
				img = Image.open(im_path)
				arr = np.array(img)
				arr2= arr.reshape([arr.shape[0]*arr.shape[1]*arr.shape[2],1])
				imgs[pair][folder].append(arr2)
				labels[pair][folder].append(ch)


	data[pair] = {}

	data[pair]['X_train'] = np.concatenate(imgs[pair]['train'], axis = 1).T
	data[pair]['X_test']  = np.concatenate(imgs[pair]['val'], axis = 1).T
	data[pair]['y_train'] = np.array([ch_map[pair][ch] for ch in labels[pair]['train']])
	data[pair]['y_test']  = np.array([ch_map[pair][ch] for ch in labels[pair]['val']])

print('Loading data is complete.')

## Tune KNN 
def tune_KNN(X_train, X_test, y_train, y_test):
	K = range(1,20)
	error_knn = []

	for k in K:
		if (k % 10 == 0): print(k)
		clf = KNeighborsClassifier(k).fit(X_train, y_train)
		y_test_pred = clf.predict(X_test)
		error_knn.append(1 - accuracy_score(y_test, y_test_pred))

	return K, error_knn


## Plot params vs. error 
fig, ax = plt.subplots()
i=0
for (pair, p_data) in data.items():
	print(pair)
	K, error = tune_KNN(p_data['X_train'], 
		p_data['X_test'], 
		p_data['y_train'], 
		p_data['y_test'])
	ax = plt.subplot(1, len(pairs), i+1)
	ax.set_title(pair)
	ax.set_xlabel('k')
	ax.set_ylabel('test error')
	ax.plot(K, error)
	i = i + 1

fig.suptitle('KNN: Test error vs. num_neighbors')
	

	# plt.figure()
	# plt.title(f'{pair}: KNN Test Error')
	# plt.xlabel('k')
	# plt.ylabel('Test Error')
	# plt.plot(K, error_knn)
	

plt.show()















# names = ["Nearest Neighbors"
# 		, "Logistic Regression"
# 		, "SVM"
# 		, "Kernel SVM"]

# classifiers = [KNeighborsClassifier(3)
# 	, LogisticRegression(max_iter = 1000)
# 	, SVC(kernel='linear')
# 	, SVC(kernel='rbf')]


# accuracy = {}
# confusion_mat = {}
# f1  = {}
# recall = {}

# for name, clf in zip(names, classifiers):

# 	# Fit model

# 	print(name)
# 	t0 = time.time()
# 	clf.fit(X_train, y_train)
# 	y_test_pred = clf.predict(X_test)
# 	t1 = time.time()
# 	print("Run time =", t1-t0)

# 	# Confusion matrix

# 	confusion_mat[name] = confusion_matrix(y_test, y_test_pred)
# 	print(confusion_mat[name])
# 	plt.figure()
# 	sns.heatmap(confusion_mat[name], annot=True, fmt='.0f')
# 	plt.title(name)


# 	# Scores

# 	report  = classification_report(y_test, y_test_pred)
# 	accuracy[name] =  classification_report(y_test, y_test_pred, output_dict=True)['weighted avg']['precision']
# 	f1[name] = classification_report(y_test, y_test_pred, output_dict=True)['weighted avg']['f1-score']
# 	recall[name] = classification_report(y_test, y_test_pred, output_dict=True)['weighted avg']['recall']

# 	print(report)

# #plt.show()
